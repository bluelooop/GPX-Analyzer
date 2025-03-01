import os
import anthropic


def generate_segment_description(segment_data: dict, prompt_str: str) -> str:
    """Generate a brief description of the segment in Spanish using Claude AI"""
    system_prompt = f""" Your are an helpful assistant in analyze route segments.
            This is the segment #{segment_data['number']} of a route:
                - Distance: {segment_data['distance']:.2f} km
                - Elevation gain: {segment_data['elevation_gain']:.0f} m
                - Elevation loss: {segment_data['elevation_loss']:.0f} m
                - Average grade: {segment_data['avg_grade']:.1f}%
                - Maximum grade: {segment_data['max_grade']:.1f}%
                - Minimum grade: {segment_data['min_grade']:.1f}%
    """

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=os.getenv('AI_MODEL'),
            temperature=1,
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": prompt_str,
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error Generating description: {e}")
        return "-"
