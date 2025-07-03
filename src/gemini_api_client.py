#!/usr/bin/env python3
"""
Direct Gemini API Client for MCP Server

This module provides direct access to the Gemini API, avoiding the 
schema compatibility issues with the current Gemini CLI.
"""

import os
import json
import asyncio
import aiohttp
from typing import Any, Dict, List, Optional
from pathlib import Path


class GeminiAPIClient:
    """Direct client for Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-1.5-flash"  # Use Flash model for higher quotas
    
    async def generate_content(self, prompt: str, context_files: List[str] = None) -> str:
        """Generate content using the Gemini API"""
        
        # Build the request payload
        contents = [{"parts": [{"text": prompt}]}]
        
        # Add context from files if provided
        if context_files:
            for file_path in context_files:
                try:
                    file_content = await self._read_file_content(file_path)
                    if file_content:
                        contents[0]["parts"].append({
                            "text": f"\n\nFile: {file_path}\n```\n{file_content}\n```"
                        })
                except Exception as e:
                    # Log but don't fail the entire request
                    contents[0]["parts"].append({
                        "text": f"\n\nNote: Could not read file {file_path}: {str(e)}"
                    })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
            }
        }
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params={"key": self.api_key},
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            return candidate["content"]["parts"][0].get("text", "No response generated")
                    return "No response generated"
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error ({response.status}): {error_text}")
    
    async def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content with proper encoding handling"""
        try:
            path_obj = Path(file_path)
            if not path_obj.exists() or not path_obj.is_file():
                return None
            
            # Limit file size to avoid oversized prompts
            if path_obj.stat().st_size > 100000:  # 100KB limit
                return f"File too large ({path_obj.stat().st_size} bytes), content truncated"
            
            with open(path_obj, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(path_obj, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None
    
    async def chat_with_context(self, message: str, working_directory: str = ".") -> str:
        """Chat with Gemini with project context"""
        
        # Look for context files (like GEMINI.md)
        context_files = []
        working_path = Path(working_directory)
        
        # Check for common context files
        for context_file in ["GEMINI.md", "README.md", ".gemini/settings.json"]:
            file_path = working_path / context_file
            if file_path.exists():
                context_files.append(str(file_path))
        
        # Enhanced prompt with context awareness
        enhanced_prompt = f"""
You are an expert AI assistant helping with development tasks. 

Working directory: {working_directory}
User request: {message}

Please provide a helpful, detailed response. If this involves code, please:
1. Consider the project context from any provided files
2. Follow best practices for the detected language/framework
3. Provide complete, working examples when applicable
4. Explain your reasoning

Request: {message}
"""
        
        return await self.generate_content(enhanced_prompt, context_files)
    
    async def analyze_code(self, directory: str, query: str) -> str:
        """Analyze code in a directory"""
        
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return f"Error: Directory {directory} does not exist or is not a directory"
        
        # Find relevant code files
        code_files = []
        for pattern in ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.go", "*.rs"]:
            code_files.extend(dir_path.glob(pattern))
            code_files.extend(dir_path.glob(f"**/{pattern}"))
        
        # Limit number of files to avoid oversized prompts
        code_files = code_files[:10]
        
        prompt = f"""
Analyze the code in directory: {directory}

Analysis request: {query}

Please examine the provided code files and give a comprehensive analysis addressing the specific query.
Focus on:
1. Code structure and organization
2. Potential issues or improvements
3. Best practices adherence
4. Specific insights related to: {query}

Please provide actionable recommendations.
"""
        
        return await self.generate_content(prompt, [str(f) for f in code_files])
    
    async def code_assistance(self, file_path: str, task: str) -> str:
        """Get code assistance for a specific file"""
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return f"Error: File {file_path} does not exist"
        
        prompt = f"""
Code assistance request for file: {file_path}

Task: {task}

Please help with the specified task. Provide:
1. Clear explanation of what needs to be done
2. Specific code changes or suggestions
3. Complete code examples where applicable
4. Best practices and reasoning

Focus specifically on: {task}
"""
        
        return await self.generate_content(prompt, [file_path])
    
    async def git_assistance(self, repository_path: str, operation: str) -> str:
        """Get Git assistance"""
        
        repo_path = Path(repository_path)
        if not repo_path.exists():
            return f"Error: Repository path {repository_path} does not exist"
        
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            return f"Error: {repository_path} is not a Git repository"
        
        # Try to get some git context
        context_files = []
        
        # Look for common files that provide context
        for file_name in [".gitignore", "README.md", "CONTRIBUTING.md"]:
            file_path = repo_path / file_name
            if file_path.exists():
                context_files.append(str(file_path))
        
        prompt = f"""
Git repository assistance for: {repository_path}

Operation requested: {operation}

Please help with the Git operation. Provide:
1. Clear step-by-step instructions
2. Exact Git commands to run
3. Explanation of what each command does
4. Potential risks or considerations
5. Best practices for this operation

Repository context will be provided from available files.
"""
        
        return await self.generate_content(prompt, context_files)
    
    async def generate_application(self, description: str, output_directory: str, framework: str = "") -> str:
        """Generate an application"""
        
        # Ensure output directory exists
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        
        framework_context = f" using {framework}" if framework else ""
        
        prompt = f"""
Generate a complete application{framework_context} based on this description:

{description}

Output directory: {output_directory}

Please provide:
1. Complete project structure
2. All necessary files with full content
3. Installation/setup instructions  
4. Usage examples
5. Best practices implementation

The application should be production-ready with proper error handling, documentation, and following current best practices.
"""
        
        return await self.generate_content(prompt)
    
    async def list_models(self) -> Dict[str, Any]:
        """List available Gemini models"""
        
        url = f"{self.base_url}/models"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"key": self.api_key}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter for Gemini models only
                    gemini_models = []
                    for model in data.get("models", []):
                        if "gemini" in model.get("name", "").lower():
                            gemini_models.append({
                                "id": model["name"].replace("models/", ""),
                                "name": model.get("displayName", model["name"].replace("models/", "")),
                                "description": model.get("description", "Gemini AI Model"),
                                "version": model.get("version", "1.0"),
                                "inputTokenLimit": model.get("inputTokenLimit", 30720),
                                "outputTokenLimit": model.get("outputTokenLimit", 2048),
                                "supportedMethods": model.get("supportedGenerationMethods", ["generateContent"])
                            })
                    
                    return {
                        "success": True,
                        "models": gemini_models,
                        "count": len(gemini_models)
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Failed to fetch models: {response.status} - {error_text}",
                        "models": []
                    }
