#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Qwen Omni model on Hathora
Uses direct HTTP API for speech-to-speech
"""

import requests
import base64
import sys
import os
import json

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Hathora API Configuration
HATHORA_API_KEY = "hathora_org_st_xOss99ULfZm2YXse50h0HRlrgrh8JMKjgiRdOxQoAHtfYPxWOJ_8299623279d9d48ec8ae15be4a922d73"
HATHORA_ENDPOINT = "https://app-478fb728-9258-44fd-95fc-d8f759205456.app.hathora.dev/v1/speech-to-speech"

class QwenOmniTester:
    def __init__(self, api_key: str, endpoint: str):
        """Initialize with API credentials"""
        self.api_key = api_key
        self.endpoint = endpoint
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        print("[OK] Qwen Omni tester initialized")
        print(f"[INFO] Endpoint: {endpoint}")

    def test_speech_to_speech(self, prompt: str, output_file: str, speaker: str = "Ethan", audio_file: str = None) -> bool:
        """Test speech-to-speech conversion"""
        print(f"\n{'='*60}")
        print(f"Test Prompt: '{prompt}'")
        print(f"Speaker: {speaker}")
        if audio_file:
            print(f"Input Audio: {audio_file}")
        print(f"Output: {output_file}")
        print('='*60)

        try:
            # Prepare content - text instruction
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            # Prepare request payload
            payload = {
                "conversation": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "speaker": speaker,
                "max_new_tokens": 512
            }

            # If audio file provided, add it at root level
            if audio_file and os.path.exists(audio_file):
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()
                    audio_base64_str = base64.b64encode(audio_data).decode('utf-8')
                    payload["audio_base64"] = audio_base64_str

            print("\n[INFO] Sending request to Qwen Omni...")

            # Make POST request
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                print("[OK] Response received")

                # Parse JSON response
                result = response.json()

                # Decode base64 audio
                audio_base64 = result.get('audio_base64')
                if not audio_base64:
                    print("[ERROR] No audio_base64 in response")
                    print(f"Response: {json.dumps(result, indent=2)}")
                    return False

                # Decode and save audio
                audio_data = base64.b64decode(audio_base64)

                with open(output_file, 'wb') as f:
                    f.write(audio_data)

                file_size = os.path.getsize(output_file)
                print(f"[OK] Audio saved to: {output_file}")
                print(f"[INFO] File size: {file_size:,} bytes")

                # Show additional metadata if available
                if 'text_response' in result:
                    print(f"[INFO] Text response: {result['text_response']}")

                return True
            else:
                print(f"[ERROR] Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_all_tests(self, output_dir: str = "output"):
        """Run all test cases"""
        print("="*60)
        print("Hathora Qwen Omni Speech-to-Speech Test Suite")
        print("="*60)
        print(f"API Key: {self.api_key[:30]}...{self.api_key[-10:]}")
        print(f"Output Directory: {output_dir}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Test cases
        test_cases = [
            {
                "prompt": "Hello! Can you tell me what the capital of France is?",
                "speaker": "Ethan",
                "audio": "test_input.wav",
                "output": os.path.join(output_dir, "test1_france.wav")
            },
            {
                "prompt": "Explain quantum computing in simple terms.",
                "speaker": "Lily",
                "audio": "test_input.wav",
                "output": os.path.join(output_dir, "test2_quantum.wav")
            },
            {
                "prompt": "Tell me a short joke about programming.",
                "speaker": "Ethan",
                "audio": "test_input.wav",
                "output": os.path.join(output_dir, "test3_joke.wav")
            },
            {
                "prompt": "What are the main features of the Qwen Omni model?",
                "speaker": "Lily",
                "audio": "test_input.wav",
                "output": os.path.join(output_dir, "test4_features.wav")
            }
        ]

        successful_tests = 0
        total_tests = len(test_cases)

        for i, test in enumerate(test_cases, 1):
            print(f"\n[TEST {i}/{total_tests}]")
            result = self.test_speech_to_speech(
                prompt=test["prompt"],
                output_file=test["output"],
                speaker=test["speaker"],
                audio_file=test.get("audio")
            )
            if result:
                successful_tests += 1

        print("\n" + "="*60)
        print(f"Test suite completed: {successful_tests}/{total_tests} tests passed")
        print("="*60)

        if successful_tests > 0:
            print("\nGenerated audio files:")
            for test in test_cases:
                if os.path.exists(test["output"]):
                    size = os.path.getsize(test["output"])
                    print(f"  - {test['output']} ({size:,} bytes)")


def main():
    """Main entry point"""
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"

    print("="*60)
    print("Hathora Qwen Omni Test Script")
    print("="*60)
    print(f"\nOutput directory: {output_dir}")
    print("\nThis script will:")
    print("  1. Test the Qwen Omni speech-to-speech API")
    print("  2. Send text prompts and receive audio responses")
    print("  3. Test 4 different prompts with 2 different voices")
    print("  4. Save responses as WAV files")
    print("\n" + "="*60 + "\n")

    try:
        tester = QwenOmniTester(HATHORA_API_KEY, HATHORA_ENDPOINT)
        tester.run_all_tests(output_dir)
    except Exception as e:
        print(f"\n[FATAL] Failed to run tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
