import base64
import re
import streamlit as st
from ollama import chat


@st.cache_resource
def get_chat_model():
    "Get a cached instance of the chat model"
    return lambda messages: chat(
        model="deepseek-r1",
        messages=messages,
        stream=True,
    )

def handle_user_input():
    """Handle user input and return a response from the chat model"""
    if user_input := st.chat_input("Ask me anything!"):
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            chat_model = get_chat_model()
            stream = chat_model(st.session_state["messages"])

            thinking_content = process_thinking_phase(stream)
            response_content = process_response_phase(stream)

            st.session_state["messages"].append(
                {"role": "assistant", "content": thinking_content + response_content}
            )

def process_thinking_phase(stream):
    """Process the thinking phase of the chat model"""
    thinking_content = ""
    with st.status("Thinking...", expanded=False) as status:
        think_placeholder = st.empty()

        for chunk in stream:
            content = chunk["message"]["content"] or ""
            thinking_content += content

            if "<think>" in content:
                continue
            if "</think>" in content:
                content = content.replace("</think>", "")
                status.update(label="Thinking complete!", state="complete", expanded=False)
                break

            think_placeholder.markdown(format_reasoning_response(thinking_content))

    return thinking_content

def process_response_phase(stream):
    """Process the response phase of the chat model"""
    response_placeholder = st.empty()
    response_content = ""

    for chunk in stream:
        content = chunk["message"]["content"] or ""
        response_content += content
        response_placeholder.markdown(response_content)

    return response_content

def display_message(message):
    """Display a message in the chat interface"""
    role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(role):
        if role == "assistant":
            display_assistant_message(message["content"])
        else:
            st.markdown(message["content"])

def display_assistant_message(content):
    """Display assistant message with thinking content if present"""
    pattern = r"<think>(.*?)</think>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        thinking_content = match.group(0)
        response_content = content.replace(thinking_content, "")
        thinking_content = format_reasoning_response(thinking_content)
        with st.expander("Thinking complete!"):
            st.markdown(thinking_content)
        st.markdown(response_content)
    else:
        st.markdown(content)

def format_reasoning_response(thinking_content):
    """Format the reasoning response for display"""
    return (
        thinking_content
        .replace("<think>", "")
        .replace("</think>", "")
    )

def display_chat_history():
    """Display all previous messages in the chat history."""
    for message in st.session_state["messages"]:
        if message["role"] != "system":  # Skip system messages
            display_message(message)


def main():
    """Main function to handle the chat interface and streaming responses."""
    #render the public/deep-seek.png in the center of the page
    st.markdown("<div style='text-align: center;'><img src='data:image/png;base64,{}' width='250' style='vertical-align: -3px;'></div>".format(base64.b64encode(open("public/deep-seek.png", "rb").read()).decode()), unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>With thinking UI! 💡</h4>", unsafe_allow_html=True)
    
    display_chat_history()
    handle_user_input()

if __name__ == "__main__":
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
    main()