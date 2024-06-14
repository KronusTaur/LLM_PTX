import re
import ollama

def extract_items(input_string):
    result_items = []
    items = input_string.split('|')[1:]
    items = [item.replace("\n", "") for item in items]
    items = [re.sub(r'^"$-', '', item) for item in items]
    for item in items:
        item = item.replace('"', '')
        if re.search('[а-яА-Я]', item):
            result_items.append(item)
    items = list(filter(None, result_items))
    return items


def slide_data_gen(topic, slide_count):
    slide_data = []
    response = ollama.chat(model='mistral', messages=[
    {
        'role': 'user',
        'content': f"""
        You are a text summarization and formatting specialized model that fetches relevant information


        Convert this text "{topic}" into a presentation, create a title, subtitle and number of slides  "{slide_count}" in russian  and also write comments for each slide in russian and  it should be returned in the format :
        | "title" | "subtitle | "slide title" | slide comments | "slide title" | slide comments | "slide title" | slide comments | ...
        """
    },
    ])
    slide_data = extract_items(response['message']['content'])
    return slide_data
