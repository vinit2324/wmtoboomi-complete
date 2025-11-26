"""
AI Assistant service for migration help.
Supports OpenAI, Anthropic, Gemini, and Ollama.
"""
from typing import Optional, List, Dict, Any
import json
import httpx

from app.models import (
    LLMSettings,
    AIRequest,
    AIResponse,
    GroovyGenerationRequest,
    GroovyGenerationResponse,
    WMPublicMappingRequest,
    WMPublicMappingResponse,
    ParsedData,
)


# System prompts
MIGRATION_SYSTEM_PROMPT = """You are an expert in migrating webMethods Integration Server applications to Dell Boomi.

Key knowledge:
1. webMethods Flow Services use only 9 verbs: MAP, BRANCH, LOOP, REPEAT, SEQUENCE, Try/Catch, Try/Finally, Catch, Finally, EXIT
2. Everything else in webMethods is done by calling services from wMPublic package (100s of built-in services)
3. Boomi has only 22 shapes/steps but handles many things implicitly
4. webMethods has manual pipeline/heap management; Boomi handles this automatically
5. webMethods LOOPs require explicit iteration; Boomi iterates implicitly

Your role:
- Help map wMPublic services to Boomi equivalents
- Explain how to convert flow verbs to Boomi shapes
- Generate Groovy scripts from Java service logic
- Suggest field mappings between schemas
- Explain complexity and provide migration guidance

Always provide practical, actionable advice with code examples when relevant."""

GROOVY_SYSTEM_PROMPT = """You are an expert at converting webMethods Java services to Boomi Groovy scripts.

Key differences:
- Boomi uses com.boomi.execution.ExecutionUtil for context
- Data is accessed through dataContext object
- Properties are set via ExecutionUtil.setDynamicProcessProperty()
- Use dataContext.getStream() and dataContext.storeStream() for document handling

Provide clean, well-commented Groovy code that follows Boomi best practices."""

WM_PUBLIC_SYSTEM_PROMPT = """You are an expert in mapping webMethods wMPublic services to Boomi equivalents.

Provide specific Boomi configuration for each webMethods service, including:
- Which Boomi shape to use
- How to configure the shape
- Any special considerations

Be precise and provide working configurations."""


class AIService:
    """AI Assistant service supporting multiple LLM providers."""
    
    @staticmethod
    async def chat(
        settings: LLMSettings,
        request: AIRequest,
        project_context: Optional[ParsedData] = None
    ) -> AIResponse:
        """Send a chat message to the LLM."""
        
        # Build context
        messages = []
        
        # System prompt with project context
        system_content = MIGRATION_SYSTEM_PROMPT
        if project_context:
            context_summary = AIService._build_context_summary(project_context)
            system_content += f"\n\nCurrent Project Context:\n{context_summary}"
        
        messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        for msg in request.conversationHistory:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # Call LLM
        response_text = await AIService._call_llm(settings, messages)
        
        # Extract suggestions and code snippets
        suggestions = AIService._extract_suggestions(response_text)
        code_snippets = AIService._extract_code_snippets(response_text)
        
        return AIResponse(
            message=response_text,
            suggestions=suggestions,
            codeSnippets=code_snippets
        )
    
    @staticmethod
    async def generate_groovy(
        settings: LLMSettings,
        request: GroovyGenerationRequest
    ) -> GroovyGenerationResponse:
        """Generate Groovy script from Java code."""
        
        messages = [
            {"role": "system", "content": GROOVY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Convert this webMethods Java service to Boomi Groovy:

Service Name: {request.serviceName}
Description: {request.description}

Java Code:
```java
{request.javaCode}
```

Provide:
1. Complete Groovy script for Boomi Data Process shape
2. Notes on any manual adjustments needed
3. List any external dependencies or imports required"""
            }
        ]
        
        response_text = await AIService._call_llm(settings, messages)
        
        # Extract Groovy code
        groovy_code = AIService._extract_code_block(response_text, "groovy")
        if not groovy_code:
            groovy_code = AIService._extract_code_block(response_text, "")
        
        # Extract notes
        notes = []
        if "note" in response_text.lower():
            lines = response_text.split('\n')
            for line in lines:
                if line.strip().startswith(('-', '*', '•', '1', '2', '3')):
                    notes.append(line.strip().lstrip('-*•123456789. '))
        
        return GroovyGenerationResponse(
            groovyCode=groovy_code or "// Conversion requires manual review",
            notes=notes[:10],  # Limit to 10 notes
            manualReviewRequired=True
        )
    
    @staticmethod
    async def map_wm_public(
        settings: LLMSettings,
        request: WMPublicMappingRequest
    ) -> WMPublicMappingResponse:
        """Map wMPublic service to Boomi equivalent."""
        
        messages = [
            {"role": "system", "content": WM_PUBLIC_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Map this webMethods wMPublic service to Boomi:

Service: {request.serviceName}
Context: {request.context}

Provide:
1. The Boomi shape/step to use
2. How to configure it
3. Any special considerations or alternatives"""
            }
        ]
        
        response_text = await AIService._call_llm(settings, messages)
        
        # Parse response to extract structured data
        boomi_shape = "Map"  # Default
        boomi_equivalent = ""
        config = {}
        notes = []
        
        # Try to extract shape name
        shape_keywords = ['Map', 'Decision', 'ForEach', 'TryCatch', 'Stop', 'Connector', 'SetProperties', 'Notify', 'DataProcess']
        for keyword in shape_keywords:
            if keyword.lower() in response_text.lower():
                boomi_shape = keyword
                break
        
        boomi_equivalent = f"Use {boomi_shape} shape"
        
        # Extract notes from bullet points
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•')) or (len(line) > 2 and line[0].isdigit() and line[1] in '.):'):
                clean_line = line.lstrip('-*•0123456789.): ')
                if clean_line and len(clean_line) > 5:
                    notes.append(clean_line)
        
        return WMPublicMappingResponse(
            boomiEquivalent=boomi_equivalent,
            boomiShape=boomi_shape,
            configuration=config,
            notes=notes[:5]
        )
    
    @staticmethod
    async def _call_llm(settings: LLMSettings, messages: List[Dict[str, str]]) -> str:
        """Call the appropriate LLM provider."""
        
        if settings.provider == "openai":
            return await AIService._call_openai(settings, messages)
        elif settings.provider == "anthropic":
            return await AIService._call_anthropic(settings, messages)
        elif settings.provider == "gemini":
            return await AIService._call_gemini(settings, messages)
        elif settings.provider == "ollama":
            return await AIService._call_ollama(settings, messages)
        else:
            return "LLM provider not configured. Please set up an LLM in customer settings."
    
    @staticmethod
    async def _call_openai(settings: LLMSettings, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API."""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.apiKey)
            
            response = await client.chat.completions.create(
                model=settings.model or "gpt-4-turbo",
                messages=messages,
                temperature=settings.temperature,
                max_tokens=4000
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"OpenAI API error: {str(e)}"
    
    @staticmethod
    async def _call_anthropic(settings: LLMSettings, messages: List[Dict[str, str]]) -> str:
        """Call Anthropic API."""
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.apiKey)
            
            # Extract system message
            system_content = ""
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    chat_messages.append(msg)
            
            response = await client.messages.create(
                model=settings.model or "claude-3-sonnet-20240229",
                max_tokens=4000,
                system=system_content,
                messages=chat_messages
            )
            
            return response.content[0].text if response.content else ""
        except Exception as e:
            return f"Anthropic API error: {str(e)}"
    
    @staticmethod
    async def _call_gemini(settings: LLMSettings, messages: List[Dict[str, str]]) -> str:
        """Call Google Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.apiKey)
            
            model = genai.GenerativeModel(settings.model or "gemini-pro")
            
            # Combine messages into a single prompt
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "system":
                    prompt_parts.append(f"System instructions: {content}")
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
            
            prompt = "\n\n".join(prompt_parts)
            
            response = await model.generate_content_async(prompt)
            return response.text if response.text else ""
        except Exception as e:
            return f"Gemini API error: {str(e)}"
    
    @staticmethod
    async def _call_ollama(settings: LLMSettings, messages: List[Dict[str, str]]) -> str:
        """Call Ollama API."""
        try:
            base_url = settings.baseUrl or "http://localhost:11434"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{base_url}/api/chat",
                    json={
                        "model": settings.model or "llama2",
                        "messages": messages,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "")
                else:
                    return f"Ollama API error: {response.status_code}"
        except Exception as e:
            return f"Ollama API error: {str(e)}"
    
    @staticmethod
    def _build_context_summary(project_context: ParsedData) -> str:
        """Build a summary of the project context for the LLM."""
        summary_parts = []
        
        # Service counts
        service_types = {}
        for svc in project_context.services:
            service_types[svc.type] = service_types.get(svc.type, 0) + 1
        
        if service_types:
            summary_parts.append(f"Services: {', '.join(f'{v} {k}' for k, v in service_types.items())}")
        
        # Document count
        if project_context.documents:
            summary_parts.append(f"Documents: {len(project_context.documents)}")
        
        # Flow verb summary
        total_verbs = {}
        for svc in project_context.services:
            if svc.flowVerbs:
                for verb, count in svc.flowVerbs.model_dump().items():
                    if count > 0:
                        total_verbs[verb] = total_verbs.get(verb, 0) + count
        
        if total_verbs:
            summary_parts.append(f"Flow verbs used: {', '.join(f'{k}:{v}' for k, v in total_verbs.items())}")
        
        # wMPublic services
        wm_public = {}
        for svc in project_context.services:
            for inv in svc.serviceInvocations:
                if inv.package.startswith(('pub.', 'wm.')):
                    key = f"{inv.package}:{inv.service}"
                    wm_public[key] = wm_public.get(key, 0) + inv.count
        
        if wm_public:
            top_5 = sorted(wm_public.items(), key=lambda x: x[1], reverse=True)[:5]
            summary_parts.append(f"Top wMPublic services: {', '.join(f'{k}({v})' for k, v in top_5)}")
        
        return "\n".join(summary_parts) if summary_parts else "No project data available"
    
    @staticmethod
    def _extract_suggestions(text: str) -> List[str]:
        """Extract suggestions from LLM response."""
        suggestions = []
        
        # Look for numbered items or bullet points
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Check for suggestions or recommendations
            if any(word in line.lower() for word in ['suggest', 'recommend', 'consider', 'could', 'should']):
                if len(line) > 20 and len(line) < 200:
                    suggestions.append(line)
        
        return suggestions[:5]
    
    @staticmethod
    def _extract_code_snippets(text: str) -> List[Dict[str, str]]:
        """Extract code snippets from LLM response."""
        snippets = []
        
        # Find code blocks
        import re
        code_pattern = r'```(\w*)\n(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        for lang, code in matches:
            snippets.append({
                "language": lang or "text",
                "code": code.strip()
            })
        
        return snippets
    
    @staticmethod
    def _extract_code_block(text: str, language: str) -> str:
        """Extract a specific code block from text."""
        import re
        
        if language:
            pattern = rf'```{language}\n(.*?)```'
        else:
            pattern = r'```\n(.*?)```'
        
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Try without language specifier
        pattern = r'```(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return ""
