// This file encapsulates all the SDL-aware code for the AudioOutput class.

#include <stdio.h>
#include <SDL2/SDL.h>

// Requested number of samples for the audio output buffer
#define BLOCK_SIZE 4096


// Instance data for the AudioOutput class, representing an open audio device.
// Each AudioOutput Python object has an opaque pointer to one of these.
typedef struct {
    SDL_AudioDeviceID audio_device;
    SDL_AudioSpec audio_spec;

    // The AudioOutput object instance
    void *audio_output_instance;

    // The method of AudioOutput to call to fill the output buffer
    void (*write_samples_callback) (void *instance, float *block, int sample_count);

    /* We call The SDL functions to play, pause, and close the audio device
     * from a separate thread, the command_executor_thread.
     * This is because calling these functions from the Python main thread
     * can cause a deadlock involving the GIL, SDL's audio device lock,
     * and two threads needing access to both
     * (the main Python thread, and the audio callback thread,
     * which calls into Python).
     *
     * To execute a command,
     * the main thread sets the `command` variable,
     * then signals the command_executor_thread using the command_semaphore.
     * The command_executor_thread wakes up
     * and calls the appropriate SDL function.
     */
    SDL_Thread *command_executor_thread;
    SDL_sem *command_semaphore;
    SDL_atomic_t command;

} AudioOutputHandle;


// Commands to be executed by the command_executor_thread
enum {NONE, PLAY, PAUSE, CLOSE};


static void sdl_audio_callback(void *audio_output_handle, Uint8 *stream, int len);
static int command_executor(void *audio_output_handle);
static void submit_command(AudioOutputHandle *handle, int command);
static void close_device_and_free_resources();


// Open an audio device with the given number of channels and samplerate
// and return a handle to the open device
AudioOutputHandle *audiooutput_sdl_new(int channels, int samplerate)
{
    AudioOutputHandle *handle = calloc(1, sizeof(AudioOutputHandle));

    if (!SDL_WasInit(SDL_INIT_AUDIO)) {
        SDL_Init(SDL_INIT_AUDIO);
    }

    SDL_AudioSpec want, have;
    SDL_memset(&want, 0, sizeof(want));
    want.freq = samplerate;
    want.format = AUDIO_F32;
    want.channels = channels;
    want.samples = BLOCK_SIZE;
    want.callback = sdl_audio_callback;
    want.userdata = (void *) handle;

    handle->audio_device = SDL_OpenAudioDevice(NULL, 0, &want, &have, 0);
    handle->audio_spec = have;

    handle->command_semaphore = SDL_CreateSemaphore(0);
    SDL_CreateThread(command_executor, "audio-command", (void *) handle);

    return handle;
}


// Set the callback function -- a method of the AudioOutput class --
// that will fill the audio output block.
// `audio_output_instance` is the AudioOutput Python object,
// and `callback` is its callback method.
void audiooutput_sdl_set_write_samples_callback(
        AudioOutputHandle *handle,
        void *audio_output_instance,
        void (*callback) (void *instance, float *block, int sample_count))
{
    handle->audio_output_instance = audio_output_instance;
    handle->write_samples_callback = callback;
}


// Start audio playback (safe to call from Python)
void audiooutput_sdl_play(AudioOutputHandle *handle)
{
    submit_command(handle, PLAY);
}


// Pause audio playback (safe to call from Python)
void audiooutput_sdl_pause(AudioOutputHandle *handle)
{
    submit_command(handle, PAUSE);
}


// Close audio device and free resources (safe to call from Python).
// `handle` should be treated as invalid after this is called.
void audiooutput_sdl_close(AudioOutputHandle *handle)
{
    submit_command(handle, CLOSE);
}


// This is needed to change the driver
// (e.g. from 'dummy' to 'disk' in unit tests)
void audiooutput_sdl_reinitialize()
{
    if (SDL_WasInit(SDL_INIT_AUDIO)) {
        SDL_QuitSubSystem(SDL_INIT_AUDIO);
    }
    SDL_Init(SDL_INIT_AUDIO);
}


// Called by SDL's audio thread
// to fill the output buffer `stream` with `len` bytes of audio data.
// This in turn calls the callback function supplied
// via audiooutput_sdl_set_write_samples_callback().
static void sdl_audio_callback(void *audio_output_handle, Uint8 *stream, int len)
{
    AudioOutputHandle *handle = (AudioOutputHandle *) audio_output_handle;
    if (handle->write_samples_callback == NULL) {
        return;
    }
    int sample_count = len / sizeof(float);
    handle->write_samples_callback(
            handle->audio_output_instance,
            (float *) stream,
            sample_count);
}


// Submit a command (PLAY, PAUSE, or CLOSE)
// to the command_executor_thread.
static void submit_command(AudioOutputHandle *handle, int command)
{
    SDL_AtomicSet(&(handle->command), command);

    // Signal the command_executor_thread
    if (SDL_SemPost(handle->command_semaphore) != 0) {
        fprintf(stderr, "SDL_SemPost failed: %s\n", SDL_GetError());
    }
}


// Main loop of the command_executor_thread
static int command_executor(void *audio_output_handle)
{
    AudioOutputHandle *handle = (AudioOutputHandle *) audio_output_handle;
    int command;

    while (1) {
        SDL_SemWait(handle->command_semaphore);
        command = SDL_AtomicGet(&(handle->command));
        if (command == PLAY) {
            SDL_PauseAudioDevice(handle->audio_device, 0);
        } else if (command == PAUSE) {
            SDL_PauseAudioDevice(handle->audio_device, 1);
        } else if (command == CLOSE) {
            close_device_and_free_resources(handle);
            break;
        }
    }

    return 0;
}


// Stop playing audio, release the device,
// and free the handle and associated resources.
static void close_device_and_free_resources(AudioOutputHandle *handle)
{
    SDL_CloseAudioDevice(handle->audio_device);
    SDL_DestroySemaphore(handle->command_semaphore);
    free(handle);
}
