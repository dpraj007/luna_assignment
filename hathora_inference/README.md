# Hathora Qwen Omni Speech-to-Speech Inference

**✅ Status: FULLY WORKING - All tests pass successfully with real API responses**

This directory contains a working implementation for testing the Qwen Omni model on Hathora using the speech-to-speech API.

## Setup

1. Install dependencies:
```bash
pip install requests
```

2. The script is ready to run with embedded API credentials

## Usage

Run the test script:

```bash
# Use default output directory (./output)
python test_qwen_omni.py

# Specify custom output directory
python test_qwen_omni.py my_audio_outputs
```

## What the Script Tests

1. **Speech-to-Speech API**: Sends text prompts with audio input and receives audio responses
2. **Multiple Voices**: Tests both "Ethan" and "Lily" voices
3. **Audio Generation**: Generates WAV audio files from text prompts
4. **4 Test Cases**: Different prompts to validate various response lengths

## Test Cases

The script runs these prompts:
1. "Hello! Can you tell me what the capital of France?" (Ethan voice)
2. "Explain quantum computing in simple terms." (Lily voice)
3. "Tell me a short joke about programming." (Ethan voice)
4. "What are the main features of the Qwen Omni model?" (Lily voice)

## Sample Output

```
============================================================
Hathora Qwen Omni Test Script
============================================================

Output directory: output

This script will:
  1. Test the Qwen Omni speech-to-speech API
  2. Send text prompts and receive audio responses
  3. Test 4 different prompts with 2 different voices
  4. Save responses as WAV files

============================================================

[OK] Qwen Omni tester initialized
[INFO] Endpoint: https://app-478fb728-9258-44fd-95fc-d8f759205456.app.hathora.dev/v1/speech-to-speech
============================================================
Hathora Qwen Omni Speech-to-Speech Test Suite
============================================================
API Key: hathora_org_st_xOss99ULfZ...e4a922d73
Output Directory: output

[TEST 1/4]

============================================================
Test Prompt: 'Hello! Can you tell me what the capital of France is?'
Speaker: Ethan
Input Audio: test_input.wav
Output: output\test1_france.wav
============================================================

[INFO] Sending request to Qwen Omni...
[OK] Response received
[OK] Audio saved to: output\test1_france.wav
[INFO] File size: 16,848 bytes

...

============================================================
Test suite completed: 4/4 tests passed
============================================================

Generated audio files:
  - output\test1_france.wav (16,848 bytes)
  - output\test2_quantum.wav (969,264 bytes)
  - output\test3_joke.wav (42,192 bytes)
  - output\test4_features.wav (521,136 bytes)
```

## API Details

The script uses direct HTTP API calls to Hathora:
- Endpoint: `/v1/speech-to-speech`
- Method: POST with JSON payload
- Input: Text prompts + base64-encoded audio
- Output: Base64-encoded audio (WAV format)
- Headers: `x-api-key` for authentication

## Technical Details

- Input audio is required (uses a silent WAV file for testing)
- Supports multiple speaker voices (Ethan, Lily, etc.)
- Responses are returned as base64-encoded audio
- Audio is automatically decoded and saved as WAV files

## Request Format

```json
{
  "conversation": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Your prompt here"
        }
      ]
    }
  ],
  "speaker": "Ethan",
  "max_new_tokens": 512,
  "audio_base64": "<base64-encoded-audio>"
}
```

## Response Format

```json
{
  "audio_base64": "<base64-encoded-wav-audio>"
}
```

## Files

- `test_qwen_omni.py` - Main test script with embedded credentials
- `requirements.txt` - Python dependencies
- `test_input.wav` - Silent test audio input (auto-generated)
- `output/` - Generated audio responses (created on first run)

## Notes

- ✅ API key and endpoint are embedded in the script
- ✅ Test input audio file is automatically created if missing
- ✅ Windows console encoding is handled automatically
- ✅ Output directory is created automatically if it doesn't exist
- ✅ All 4 tests pass successfully with real API responses

## Verified Working

**Last tested**: December 4, 2024
- ✅ All 4 tests passed
- ✅ Generated audio files playable and valid
- ✅ Multiple voices (Ethan, Lily) working correctly
