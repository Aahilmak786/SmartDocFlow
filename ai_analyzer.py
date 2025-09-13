import openai
from typing import List, Dict, Any, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
from datetime import datetime

from app.core.config import settings
from app.models.document import DocumentSearchResult

class AIAnalyzer:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4"
    
    async def analyze_document_content(self, content: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze document content using OpenAI GPT-4"""
        try:
            if not content:
                return {"error": "No content to analyze"}
            
            # Truncate content if too long (GPT-4 has token limits)
            max_tokens = 8000
            if len(content) > max_tokens * 4:  # Rough estimate: 1 token ≈ 4 characters
                content = content[:max_tokens * 4] + "..."
            
            # Define analysis prompts based on type
            prompts = {
                "general": f"""
                Analyze the following document content and provide insights:
                
                {content}
                
                Please provide:
                1. Key topics and themes
                2. Main entities (people, organizations, locations)
                3. Document type and purpose
                4. Key insights and findings
                5. Summary (2-3 sentences)
                6. Suggested tags for categorization
                
                Format your response as JSON with the following structure:
                {{
                    "topics": ["topic1", "topic2"],
                    "entities": {{
                        "people": ["person1", "person2"],
                        "organizations": ["org1", "org2"],
                        "locations": ["location1", "location2"]
                    }},
                    "document_type": "type",
                    "purpose": "purpose description",
                    "key_insights": ["insight1", "insight2"],
                    "summary": "brief summary",
                    "tags": ["tag1", "tag2"]
                }}
                """,
                
                "legal": f"""
                Analyze the following legal document content:
                
                {content}
                
                Please provide:
                1. Document type (contract, agreement, policy, etc.)
                2. Parties involved
                3. Key terms and conditions
                4. Important dates and deadlines
                5. Legal implications
                6. Risk assessment
                7. Action items required
                
                Format as JSON with structure:
                {{
                    "document_type": "type",
                    "parties": ["party1", "party2"],
                    "key_terms": ["term1", "term2"],
                    "important_dates": ["date1", "date2"],
                    "legal_implications": ["implication1", "implication2"],
                    "risk_level": "low/medium/high",
                    "action_items": ["action1", "action2"]
                }}
                """,
                
                "financial": f"""
                Analyze the following financial document content:
                
                {content}
                
                Please provide:
                1. Document type (report, statement, invoice, etc.)
                2. Financial figures and amounts
                3. Key metrics and ratios
                4. Trends and patterns
                5. Financial health indicators
                6. Recommendations
                
                Format as JSON with structure:
                {{
                    "document_type": "type",
                    "financial_figures": ["figure1", "figure2"],
                    "key_metrics": ["metric1", "metric2"],
                    "trends": ["trend1", "trend2"],
                    "health_indicators": ["indicator1", "indicator2"],
                    "recommendations": ["rec1", "rec2"]
                }}
                """,
                
                "technical": f"""
                Analyze the following technical document content:
                
                {content}
                
                Please provide:
                1. Document type (specification, manual, report, etc.)
                2. Technical concepts and technologies
                3. System architecture components
                4. Technical requirements
                5. Implementation details
                6. Technical challenges and solutions
                
                Format as JSON with structure:
                {{
                    "document_type": "type",
                    "technologies": ["tech1", "tech2"],
                    "architecture_components": ["component1", "component2"],
                    "requirements": ["req1", "req2"],
                    "implementation_details": ["detail1", "detail2"],
                    "challenges": ["challenge1", "challenge2"]
                }}
                """
            }
            
            prompt = prompts.get(analysis_type, prompts["general"])
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert document analyst. Provide accurate, detailed analysis in the requested JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse JSON response
            analysis_text = response.choices[0].message.content
            try:
                analysis = json.loads(analysis_text)
                return analysis
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                return {"raw_analysis": analysis_text}
                
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def compare_documents(self, documents: List[DocumentSearchResult]) -> Dict[str, Any]:
        """Compare multiple documents and find similarities/differences"""
        try:
            if len(documents) < 2:
                return {"error": "Need at least 2 documents to compare"}
            
            # Prepare document content for comparison
            doc_contents = []
            for i, doc in enumerate(documents[:5]):  # Limit to 5 documents
                content = doc.content or ""
                if len(content) > 1000:
                    content = content[:1000] + "..."
                doc_contents.append(f"Document {i+1} ({doc.filename}): {content}")
            
            comparison_text = "\n\n".join(doc_contents)
            
            prompt = f"""
            Compare the following documents and provide analysis:
            
            {comparison_text}
            
            Please provide:
            1. Common themes and topics across documents
            2. Key differences between documents
            3. Document relationships and connections
            4. Overall insights and patterns
            5. Recommendations based on the comparison
            
            Format as JSON:
            {{
                "common_themes": ["theme1", "theme2"],
                "key_differences": ["difference1", "difference2"],
                "relationships": ["relationship1", "relationship2"],
                "insights": ["insight1", "insight2"],
                "recommendations": ["rec1", "rec2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at comparing and analyzing multiple documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            comparison_text = response.choices[0].message.content
            try:
                comparison = json.loads(comparison_text)
                return comparison
            except json.JSONDecodeError:
                return {"raw_comparison": comparison_text}
                
        except Exception as e:
            return {"error": f"Comparison failed: {str(e)}"}
    
    async def generate_summary(self, documents: List[DocumentSearchResult], summary_type: str = "executive") -> Dict[str, Any]:
        """Generate summary of multiple documents"""
        try:
            if not documents:
                return {"error": "No documents to summarize"}
            
            # Prepare content for summarization
            all_content = []
            for doc in documents[:10]:  # Limit to 10 documents
                content = doc.content or ""
                if len(content) > 500:
                    content = content[:500] + "..."
                all_content.append(f"{doc.filename}: {content}")
            
            content_text = "\n\n".join(all_content)
            
            # Define summary types
            summary_prompts = {
                "executive": "Provide an executive summary highlighting key points, decisions, and action items.",
                "detailed": "Provide a detailed summary covering all major topics, findings, and implications.",
                "actionable": "Focus on actionable insights, next steps, and recommendations.",
                "technical": "Provide a technical summary focusing on technical details, specifications, and requirements."
            }
            
            prompt_type = summary_prompts.get(summary_type, summary_prompts["executive"])
            
            prompt = f"""
            Generate a {summary_type} summary of the following documents:
            
            {content_text}
            
            {prompt_type}
            
            Format as JSON:
            {{
                "summary": "main summary text",
                "key_points": ["point1", "point2"],
                "action_items": ["action1", "action2"],
                "insights": ["insight1", "insight2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating clear, concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            summary_text = response.choices[0].message.content
            try:
                summary = json.loads(summary_text)
                return summary
            except json.JSONDecodeError:
                return {"raw_summary": summary_text}
                
        except Exception as e:
            return {"error": f"Summary generation failed: {str(e)}"}
    
    async def extract_insights(self, search_results: List[DocumentSearchResult]) -> Dict[str, Any]:
        """Extract insights from search results"""
        try:
            if not search_results:
                return {"error": "No search results to analyze"}
            
            # Analyze patterns in search results
            content_samples = []
            for result in search_results[:5]:
                content = result.content or ""
                if len(content) > 300:
                    content = content[:300] + "..."
                content_samples.append(f"Score: {result.similarity_score or result.relevance_score or 0} - {content}")
            
            analysis_text = "\n\n".join(content_samples)
            
            prompt = f"""
            Analyze these search results and extract insights:
            
            {analysis_text}
            
            Please provide:
            1. Patterns and trends in the results
            2. Quality and relevance assessment
            3. Potential gaps or missing information
            4. Suggestions for improving search
            5. Key takeaways from the results
            
            Format as JSON:
            {{
                "patterns": ["pattern1", "pattern2"],
                "quality_assessment": "assessment",
                "gaps": ["gap1", "gap2"],
                "search_improvements": ["improvement1", "improvement2"],
                "key_takeaways": ["takeaway1", "takeaway2"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing search results and extracting meaningful insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            insights_text = response.choices[0].message.content
            try:
                insights = json.loads(insights_text)
                return insights
            except json.JSONDecodeError:
                return {"raw_insights": insights_text}
                
        except Exception as e:
            return {"error": f"Insight extraction failed: {str(e)}"}

# Global AI analyzer instance
ai_analyzer = AIAnalyzer()


