import streamlit as st
import os
import json
import tempfile
from collections import Counter
from unstructured.staging.base import elements_from_json
from unstructured.documents.elements import NarrativeText, Title
from unstructured.cleaners.core import replace_unicode_quotes, clean_non_ascii_chars, clean_extra_whitespace


###########################
### Set App Variables #####
###########################

# Initialize the state variables
if 'show_python_script' not in st.session_state:
    st.session_state.show_python_script = False
if 'only_text' not in st.session_state:
    st.session_state.only_text = False
if 'apply_cleaning' not in st.session_state:  # Initialize apply_cleaning in the session state
    st.session_state.apply_cleaning = False


# Predefined category types
all_category_types = [
    'Header', 'Title', 'NarrativeText', 'Table', 'Image',
    'FigureCaption', 'ListItem', 'Address', 'Formula',
    'UncategorizedText', 'Footer', 'PageBreak'
]

# Predefined common metadata types based on the document provided
common_metadata_types = [
    'filename', 'filetype', 'page_number', 'coordinates', 'parent_id', 'category_depth',
    'languages', 'emphasized_text_contents'  # Add more as needed from your document
]

# Initialize the variables at the start of the app
categories_to_include = all_category_types  # Default value, can be empty list if preferred
metadata_to_include = []  # Default empty list
apply_cleaning = True  # Default value

###########################
###Function Definitions####
###########################

# 1. process_elements
def process_elements(uploaded_file, categories_to_include, apply_cleaning):
    with st.spinner('Processing the file...'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        elements = elements_from_json(tmp_file_path)
        os.unlink(tmp_file_path)  # Delete the temp file after use
        filtered_elements = [element for element in elements if getattr(element, 'category', None) in categories_to_include]
        if apply_cleaning:
            filtered_elements = clean_text_elements(filtered_elements)
    return filtered_elements

# 2. construct_display_text
def construct_display_text(filtered_elements, extracted_metadata_list, metadata_to_include, only_text=False, apply_cleaning=True):
    if only_text:
        return "\n\n".join([getattr(element, 'text', 'No text available') for element in filtered_elements])
    else:
        display_text = []
        for element, metadata in zip(filtered_elements, extracted_metadata_list):
            element_text = getattr(element, 'text', 'No text available')
            if apply_cleaning:
                # Clean the text of the single element
                cleaned_elements = clean_text_elements([element])
                element_text = getattr(cleaned_elements[0], 'text', 'No text available')  # Retrieve cleaned text
            element_display = f"##### {getattr(element, 'category', 'No category')} #####\n\n"
            if metadata_to_include:
                element_display += f"Metadata (Selected):\n" + "\n".join(f"{key}: {metadata.get(key, 'N/A')}" for key in metadata_to_include) + "\n\n"
            else:
                element_display += "Selected Metadata: None\n\n"
            element_display += element_text + "\n" + '-'*80
            display_text.append(element_display)
        return "\n\n".join(display_text)

# 3. Extract Metadata
def extract_selected_metadata(elements, selected_fields=None):
    """
    Extracts specified metadata fields from each element.

    :param elements: A list of document elements.
    :param selected_fields: A list of strings representing the metadata fields to extract.
                            If None or empty, all fields will be extracted.
    :return: A list of dictionaries, each containing metadata for one element.
    """
    metadata_list = []

    # Iterate through each element
    for element in elements:
        # Convert the metadata to a dictionary
        metadata = element.metadata.to_dict()
        
        # If specific fields are selected, filter the metadata
        if selected_fields:
            filtered_metadata = {field: metadata[field] for field in selected_fields if field in metadata}
            metadata_list.append(filtered_metadata)
        else:
            # If no specific fields are selected, append all metadata
            metadata_list.append(metadata)

    return metadata_list

# 4. Retrieve a list of unique metadata keys
def get_all_metadata_keys(elements):
    """
    Retrieves a list of unique metadata keys from a list of document elements.
    :param elements: A list of document elements.
    :return: A list of unique metadata keys.
    """
    all_keys = set()
    for element in elements:
        metadata = element.metadata.to_dict()
        all_keys.update(metadata.keys())
    return list(all_keys)

# 5. Get Elements From The JSON File
def get_elements_from_json_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='wb') as tmp_file:  # Use 'wb' to write binary data
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    elements = elements_from_json(tmp_file_path)
    os.unlink(tmp_file_path)
    return elements

# 6. Count The Elements By Category Type
def count_and_print_category_counts(elements):
    category_counts = Counter(getattr(element, 'category', 'Uncategorized') for element in elements)
    for category, count in category_counts.items():
        print(f"{category}: {count}")
    return category_counts

# 7. Filter The Elements By Category
def filter_elements_by_category(elements, categories_to_include):
    return [element for element in elements if getattr(element, 'category', None) in categories_to_include]

# 8. Clean The Elements
def clean_text_elements(elements):
    for element in elements:
        if hasattr(element, 'text'):
            text = getattr(element, 'text', '')
            text = replace_unicode_quotes(text)
            text = clean_non_ascii_chars(text)
            text = clean_extra_whitespace(text)
            setattr(element, 'text', text)
    return elements

# 9. Create the script for future use
def generate_python_script(categories_to_include, metadata_to_include, apply_cleaning, only_text):
    categories_str = json.dumps(categories_to_include)
    metadata_str = json.dumps(metadata_to_include)
    cleaning_str = 'True' if apply_cleaning else 'False'
    only_text_str = 'True' if only_text else 'False'

    # Generate the Python script as a string
    script = f"""
import json
import os
import glob
from collections import Counter
from unstructured.staging.base import elements_from_json
from unstructured.cleaners.core import replace_unicode_quotes, clean_non_ascii_chars, clean_extra_whitespace


###############################
### USER DEFINED VARIABLES ####
###############################

# Input file path or directory with multiple JSON files
input_path = '/input_path'  # Replace this with your file or directory path

# Output directory for saving the results
output_dir = '/output_dir'  # Replace with your output directory path

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

###############################
### USER DEFINED VARIABLES ####
###############################


###############################
### APP DEFINED VARIABLES ####
###############################

# Main Execution
categories_to_include = json.loads('{categories_str}')
metadata_to_include = json.loads('{metadata_str}')
apply_cleaning = {cleaning_str}
only_text = {only_text_str}

###############################
### APP DEFINED VARIABLES ####
###############################

# Function Definitions


# 1. construct_display_text
def construct_display_text(filtered_elements, extracted_metadata_list, metadata_to_include, only_text=False, apply_cleaning=True):
    if only_text:
        return "\\n\\n".join([getattr(element, 'text', 'No text available') for element in filtered_elements])
    else:
        display_text = []
        for element, metadata in zip(filtered_elements, extracted_metadata_list):
            element_text = getattr(element, 'text', 'No text available')
            if apply_cleaning:
                cleaned_elements = clean_text_elements([element])
                element_text = getattr(cleaned_elements[0], 'text', 'No text available')
            element_display = f"##### {{getattr(element, 'category', 'No category')}} #####\\n\\n"
            if metadata_to_include:
                element_display += "Metadata (Selected):\\n" + "\\n".join(f"{{key}}: {{metadata.get(key, 'N/A')}}" for key in metadata_to_include) + "\\n\\n"
            else:
                element_display += "Selected Metadata: None\\n\\n"
            element_display += element_text + "\\n" + '-'*80
            display_text.append(element_display)
        return "\\n\\n".join(display_text)


# 2. Extract Metadata
def extract_selected_metadata(elements, selected_fields=None):

    # Extracts specified metadata fields from each element.

    # :param elements: A list of document elements.
    # :param selected_fields: A list of strings representing the metadata fields to extract.
    #                         If None or empty, all fields will be extracted.
    # :return: A list of dictionaries, each containing metadata for one element.

    metadata_list = []

    # Iterate through each element
    for element in elements:
        # Convert the metadata to a dictionary
        metadata = element.metadata.to_dict()
        
        # If specific fields are selected, filter the metadata
        if selected_fields:
            filtered_metadata = {{field: metadata[field] for field in selected_fields if field in metadata}}
            metadata_list.append(filtered_metadata)
        else:
            # If no specific fields are selected, append all metadata
            metadata_list.append(metadata)

    return metadata_list

# 3. Retrieve a list of unique metadata keys
def get_all_metadata_keys(elements):

    # Retrieves a list of unique metadata keys from a list of document elements.
    # :param elements: A list of document elements.
    # :return: A list of unique metadata keys.

    all_keys = set()
    for element in elements:
        metadata = element.metadata.to_dict()
        all_keys.update(metadata.keys())
    return list(all_keys)

# 4. Get Elements From The JSON File
def get_elements_from_json_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='wb') as tmp_file:  # Use 'wb' to write binary data
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    elements = elements_from_json(tmp_file_path)
    os.unlink(tmp_file_path)
    return elements

# 5. Count The Elements By Category Type
def count_and_print_category_counts(elements):
    category_counts = Counter(getattr(element, 'category', 'Uncategorized') for element in elements)
    for category, count in category_counts.items():
        print(f"{{category}}: {{count}}")
    return category_counts

# 6. Filter The Elements By Category
def filter_elements_by_category(elements, categories_to_include):
    return [element for element in elements if getattr(element, 'category', None) in categories_to_include]

# 7. Clean The Elements
def clean_text_elements(elements):
    for element in elements:
        if hasattr(element, 'text'):
            text = getattr(element, 'text', '')
            text = replace_unicode_quotes(text)
            text = clean_non_ascii_chars(text)
            text = clean_extra_whitespace(text)
            setattr(element, 'text', text)
    return elements

# 8. Processing a JSON file
def process_json_file(file_path, categories_to_include, apply_cleaning, output_dir):
    elements = elements_from_json(file_path)
    filtered_elements = [element for element in elements if getattr(element, 'category', None) in categories_to_include]
    if apply_cleaning:
        filtered_elements = clean_text_elements(filtered_elements)
    
    extracted_metadata_list = extract_selected_metadata(filtered_elements, metadata_to_include)
    display_text = construct_display_text(filtered_elements, extracted_metadata_list, metadata_to_include, only_text=only_text, apply_cleaning=apply_cleaning)
    
    # Save the output to a file in the output directory
    output_file = os.path.join(output_dir, os.path.basename(file_path).replace('.json', '_output.txt'))
    with open(output_file, 'w') as f:
        f.write(display_text)

# 9. Check if path or directory, then handle accordingly
def process_path(path):
    if os.path.isfile(path) and path.endswith('.json'):
        process_json_file(path, categories_to_include, apply_cleaning, output_dir)
    elif os.path.isdir(path):
        for file in glob.glob(os.path.join(path, '*.json')):
            process_json_file(file, categories_to_include, apply_cleaning, output_dir)



# Process the file(s)
process_path(input_path)
"""

    return script



#######################################
### Streamlit app layout and logic ####
#######################################

st.title('Visual Editor For Unstructured JSON')


# Clear Instructions & Visual Hierarchy
st.markdown("## Instructions")
st.markdown("""
- **Upload a JSON File**: Choose a JSON file to process.
- **Metadata Options**: Select metadata fields to include in the output.
- **Filter Element Types & Text**: Select specific element types to filter and whether to clean the text.
- **Views**: Toggle between different views of the data or the generated Python script.
""")

# Layout Organization - Grouping related controls
with st.sidebar:
    st.subheader("Upload & Filter Options")
    uploaded_file = st.file_uploader("Choose a JSON file", type='json')

    # Filter Element Types & Text
    st.subheader("Filter Element Types & Text")
    categories_to_include = st.multiselect(
        "Select element types:", 
        options=all_category_types, 
        default=all_category_types
    )

    # Metadata options
    st.subheader("Metadata Options")
    metadata_to_include = st.multiselect(
        "Select metadata types:", 
        options=common_metadata_types, 
        default=[]
    )

    # Apply text cleaning checkbox
    apply_cleaning = st.checkbox("Apply text cleaning", value=st.session_state.apply_cleaning)
    if apply_cleaning != st.session_state.apply_cleaning:
        st.session_state.apply_cleaning = apply_cleaning

    # Toggle views
    st.subheader("Views")
    st.session_state.only_text = st.checkbox("Only Text", value=st.session_state.only_text)
    st.session_state.show_python_script = st.checkbox("Show Python Script", value=st.session_state.show_python_script)

    
    # Footer
    st.markdown("---")
    st.markdown("""
    This visual editor is:
    * Powered by **Streamlit**
    * Inspired by **Unstructured.io**'s groundbreaking work in structuring the unstructured
    * Graciously crafted for you by the innovative minds at **Hardpoint Consulting**.
                

    For feedback, suggestions, or inquiries, please reach out to us at [info@hardpointconsulting.com](mailto:info@hardpointconsulting.com).
    """)

# Main display area
text_display_area = st.empty()

if uploaded_file is not None:
    with st.spinner('Loading and processing your file...'):
        # Refactored to use the process_elements function
        filtered_elements = process_elements(uploaded_file, categories_to_include, st.session_state.apply_cleaning)
        extracted_metadata_list = extract_selected_metadata(filtered_elements, metadata_to_include)
        
        available_metadata_keys = get_all_metadata_keys(filtered_elements)  # Update available_metadata_keys with actual keys


        if st.session_state.show_python_script:
            # If the 'Show Python Script' checkbox is checked, generate and display the Python script
            generated_script = generate_python_script(categories_to_include, metadata_to_include, st.session_state.apply_cleaning, st.session_state.only_text)
            text_display_area.text_area("Python Script:", generated_script, height=500)

            # Provide a download button for the generated Python script
            st.download_button(
                label="Download Python Script",
                data=generated_script,
                file_name="generated_script.py",
                mime="text/plain"
            )
        else:
            # If the 'Show Python Script' checkbox is not checked, display the filtered text
            # Construct the display text based on the current state of only_text
            display_text = construct_display_text(filtered_elements, extracted_metadata_list, metadata_to_include, st.session_state.only_text, st.session_state.apply_cleaning)
            text_display_area.text_area("Selected Elements & Data", display_text, height=500)

            # Provide a download button for the constructed display text, if any
            if display_text:
                st.download_button(
                    label="Download text",
                    data=display_text,
                    file_name="filtered_text.txt",
                    mime="text/plain"
                )

