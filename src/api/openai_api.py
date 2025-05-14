try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIAPI:
    """
    Class to handle interactions with the OpenAI API for insight generation
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if OPENAI_AVAILABLE:
            openai.api_key = self.api_key
        self.model = "gpt-4o-mini"  # Using the model specified in the requirements
    
    def generate_founder_insight(self, profile_data, change_data):
        """
        Generate insights for a founder transition
        
        Parameters:
        - profile_data: Dictionary containing profile information
        - change_data: Dictionary containing information about the career change
        
        Returns:
        - String containing the generated insight
        """
        # Generate mock insight based on profile data
        first_name = profile_data.get('first_name', 'the founder')
        current_company = profile_data.get('current_company', 'their startup')
        previous_company = profile_data.get('previous_company', 'a tech company')
        previous_title = profile_data.get('previous_title', 'an industry role')
        
        mock_insights = [
            f"{first_name}'s background as {previous_title} at {previous_company} provides valuable industry expertise for {current_company}, making them a promising founder to connect with for early-stage investment.",
            f"With experience at {previous_company} and a transition to building {current_company}, {first_name} brings domain knowledge and entrepreneurial drive that could lead to strong investment returns.",
            f"{first_name}'s founder journey at {current_company} leverages their {previous_company} experience, suggesting market-informed innovation worth exploring for pre-seed investment.",
            f"Having made the leap from {previous_company} to founding {current_company}, {first_name} demonstrates both industry expertise and entrepreneurial ambition needed for startup success."
        ]
        
        # Use a simple hash of the profile name to deterministically select a mock insight
        name_str = f"{profile_data.get('first_name', '')}{profile_data.get('last_name', '')}"
        index = sum(ord(c) for c in name_str) % len(mock_insights) if name_str else 0
        mock_insight = mock_insights[index]
        
        # If no API key or OpenAI not available, return mock insight
        if not self.api_key or not OPENAI_AVAILABLE:
            return mock_insight
        
        # Create a prompt with the profile and change information
        prompt = self._create_insight_prompt(profile_data, change_data)
        
        try:
            # Generate insight using OpenAI API
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert venture capital analyst who identifies promising pre-seed founders to contact. Create a concise, single-sentence explanation of why a founder is worth contacting based on their profile and recent career change."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            # Extract and return the generated insight
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Return mock insight on error
            return mock_insight
    
    def _create_insight_prompt(self, profile_data, change_data):
        """
        Create a prompt for the OpenAI API based on profile and change data
        
        Parameters:
        - profile_data: Dictionary containing profile information
        - change_data: Dictionary containing information about the career change
        
        Returns:
        - String containing the prompt
        """
        # Format the profile data for the prompt
        name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}"
        current_role = profile_data.get('current_title', '')
        current_company = profile_data.get('current_company', '')
        previous_role = profile_data.get('previous_title', '')
        previous_company = profile_data.get('previous_company', '')
        
        # Extract education information
        education = profile_data.get('education', [])
        education_str = ""
        if education:
            for edu in education:
                school = edu.get('school', '')
                degree = edu.get('degree', '')
                field = edu.get('field', '')
                education_str += f"{degree} in {field} from {school}, "
            education_str = education_str.rstrip(", ")
        
        # Extract skills
        skills = profile_data.get('skills', [])
        skills_str = ", ".join(skills) if skills else ""
        
        # Create a structured prompt
        prompt = f"""
Name: {name}
Current Role: {current_role} at {current_company}
Previous Role: {previous_role} at {previous_company}
Education: {education_str}
Skills: {skills_str}

The person has recently changed from {previous_role} at {previous_company} to {current_role} at {current_company}.
Based on their background and new role, what makes them a good outreach target for pre-seed investment?
Provide one concise, actionable sentence that highlights why this founder would be valuable to connect with.
"""
        return prompt
    
    def analyze_company_potential(self, company_name, founder_background):
        """
        Analyze a new company's potential based on the founder's background
        
        Parameters:
        - company_name: Name of the company
        - founder_background: Dictionary or string describing the founder's background
        
        Returns:
        - String containing the analysis
        """
        # Create deterministic mock analysis based on company name
        previous_company = ""
        if isinstance(founder_background, dict):
            previous_company = founder_background.get('previous_company', 'an established company')
        
        mock_analyses = [
            f"{company_name} shows significant potential in the tech sector, leveraging the founder's experience at {previous_company} to solve real industry pain points with a scalable business model.",
            f"Given the founder's background at {previous_company}, {company_name} is positioned to disrupt its target market with innovative technology and a strong understanding of customer needs.",
            f"{company_name} demonstrates promising early traction, with the founder's {previous_company} experience providing valuable industry insights and potential customer connections.",
            f"As a pre-seed investment opportunity, {company_name} benefits from experienced leadership with {previous_company} domain expertise and a clear vision for product-market fit."
        ]
        
        # Deterministically select a mock analysis based on company name
        index = sum(ord(c) for c in company_name) % len(mock_analyses) if company_name else 0
        mock_analysis = mock_analyses[index]
        
        # If no API key or OpenAI not available, return mock analysis
        if not self.api_key or not OPENAI_AVAILABLE:
            return mock_analysis
            
        # Create a prompt for company analysis
        if isinstance(founder_background, dict):
            # Format the background if it's a dictionary
            background_str = f"""
Previous Role: {founder_background.get('previous_title', '')} at {founder_background.get('previous_company', '')}
Education: {', '.join([f"{edu.get('degree', '')} from {edu.get('school', '')}" for edu in founder_background.get('education', [])])}
Skills: {', '.join(founder_background.get('skills', []))}
"""
        else:
            # Use as is if it's a string
            background_str = founder_background
        
        prompt = f"""
Company Name: {company_name}
Founder Background: {background_str}

Based on the founder's background, analyze the potential of this new company. What industry is it likely in?
What problem might they be solving? What makes this venture promising for pre-seed investment?
Provide a concise analysis in 2-3 sentences.
"""
        
        try:
            # Generate analysis using OpenAI API
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert venture capital analyst specializing in early-stage startup evaluation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            # Extract and return the generated analysis
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Return mock analysis on error
            return mock_analysis
