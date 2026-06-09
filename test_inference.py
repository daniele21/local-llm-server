#!/usr/bin/env python3
"""
test_inference.py

A modular script to run batch inference tests on a local LLM server using keywords
to classify company activities into specific categories.
"""

import argparse
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration parameters from a JSON file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[-] Configuration file {config_path} not found. Using defaults.")
        return {}
    except json.JSONDecodeError as e:
        print(f"[-] Error parsing JSON in {config_path}: {e}")
        return {}

def add_user_message(element: str) -> str:
    """Formats the user prompt with the given keywords."""
    return (
        "Analyze the following keywords and return the JSON output as specified:\n\n"
        f"Keywords: {element}"
    )

def query_llm_server(
    server_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 128,
    response_format: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Sends a chat completions request to the LLM server using urllib."""
    url = f"{server_url.rstrip('/')}/chat/completions"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    if response_format:
        payload["response_format"] = response_format

    headers = {"Content-Type": "application/json"}
    req_data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
    
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = response.read().decode("utf-8")
            elapsed = time.perf_counter() - t0
            res_json = json.loads(res_data)
            
            # Extract generated content
            choices = res_json.get("choices", [])
            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "").strip()
            
            # Extract usage stats if present
            usage = res_json.get("usage", {})
            
            return {
                "success": True,
                "content": content,
                "latency_seconds": elapsed,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "error": None
            }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "content": "",
            "latency_seconds": time.perf_counter() - t0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "latency_seconds": time.perf_counter() - t0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "error": f"Unexpected error: {e}"
        }

def run_tests(config: Dict[str, Any]) -> None:
    """Iterates over all keyword lists, queries the LLM, and prints/saves results."""
    server_url = config.get("server_url", "http://127.0.0.1:8000/v1")
    model = config.get("model", "local-model")
    temperature = config.get("temperature", 0.0)
    max_tokens = config.get("max_tokens", 128)
    response_format = config.get("response_format")
    system_prompt = config.get("system_prompt", "")
    keywords_list = config.get("keywords", [])

    print("=" * 80)
    print(f"Starting inference test suite")
    print(f"Server URL:  {server_url}")
    print(f"Model:       {model}")
    print(f"Temperature: {temperature}")
    print(f"Total Rows:  {len(keywords_list)}")
    print("=" * 80)

    results = []
    success_count = 0

    for idx, keywords in enumerate(keywords_list, 1):
        user_prompt = add_user_message(keywords)
        print(f"\n[{idx}/{len(keywords_list)}] Keywords: {keywords[:60]}...")
        
        res = query_llm_server(
            server_url=server_url,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )
        
        if res["success"]:
            success_count += 1
            content = res["content"]
            # Attempt to parse response as JSON for cleaner representation
            try:
                parsed_content = json.loads(content)
                classification = parsed_content.get("classification", "N/A")
            except Exception:
                classification = content
                
            print(f"  -> Result:      \033[92m{classification}\033[0m")
            print(f"  -> Latency:     {res['latency_seconds']:.2f}s")
            print(f"  -> Tokens:      Prompt: {res['prompt_tokens']} | Completion: {res['completion_tokens']}")
            
            results.append({
                "index": idx,
                "keywords": keywords,
                "raw_response": content,
                "classification": classification,
                "latency_seconds": res["latency_seconds"],
                "prompt_tokens": res["prompt_tokens"],
                "completion_tokens": res["completion_tokens"],
                "status": "success"
            })
        else:
            print(f"  -> \033[91mFailed: {res['error']}\033[0m")
            results.append({
                "index": idx,
                "keywords": keywords,
                "error": res["error"],
                "status": "failed"
            })

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUITE SUMMARY")
    print(f"Successful runs: {success_count}/{len(keywords_list)}")
    if results:
        avg_latency = sum(r.get("latency_seconds", 0) for r in results if r["status"] == "success") / (success_count or 1)
        total_tokens = sum(r.get("completion_tokens", 0) for r in results if r["status"] == "success")
        print(f"Average Latency (success): {avg_latency:.2f}s")
        print(f"Total Completion Tokens:   {total_tokens}")
    print("=" * 80)

    # Save results to a report file
    report_file = "inference_results_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Full report saved to {report_file}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM activity classification inference tests.")
    parser.path = "test_inference.py"
    parser.add_argument(
        "--config", 
        type=str, 
        default="inference_test_config.json", 
        help="Path to the JSON configuration file"
    )
    parser.add_argument(
        "--server-url", 
        type=str, 
        help="Override server URL from config"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    if args.server_url:
        config["server_url"] = args.server_url

    if not config:
        print("[-] Invalid or missing configuration. Aborting.")
        return

    run_tests(config)

if __name__ == "__main__":
    main()
