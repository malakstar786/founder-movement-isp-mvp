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
        if not self.api_key:
            return "API key not configured. Unable to generate insight."
        
        if not OPENAI_AVAILABLE:
            return "OpenAI library not installed. Unable to generate insight."
        
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
            return f"Error generating insight: {str(e)}"
    
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
        if not self.api_key:
            return "API key not configured. Unable to perform analysis."
        
        if not OPENAI_AVAILABLE:
            return "OpenAI library not installed. Unable to perform analysis."
        
        # Mock response when OpenAI is not available
        if not OPENAI_AVAILABLE:
            return f"Based on the founder's background in {founder_background.get('previous_company', 'tech')}, this {company_name} startup shows promise in their industry sector."
        
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
            return f"Error generating analysis: {str(e)}"
