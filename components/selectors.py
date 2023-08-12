from ApiClient import ApiClient
from components.history import get_history
import streamlit as st
import os
import logging


@st.cache_data
def cached_get_extensions():
    return ApiClient.get_extensions()


skip_args = [
    "command_list",
    "context",
    "COMMANDS",
    "date",
    "conversation_history",
    "agent_name",
    "working_directory",
    "helper_agent_name",
]


def build_args(args: dict = {}, prompt: dict = {}, step_number: int = 0):
    return {
        arg: st.text_input(arg, value=prompt.get(arg, ""), key=f"{arg}_{step_number}")
        for arg in args
        if arg not in skip_args
    }


def prompt_options(prompt: dict = {}, step_number: int = 0):
    if prompt == {}:
        ops = False
    else:
        for opt in [
            "shots",
            "context_results",
            "browse_links",
            "websearch",
            "websearch_depth",
            "disable_memory",
        ]:
            if opt not in prompt:
                ops = False
                break
            else:
                ops = True
    advanced_options = st.checkbox(
        "Show Advanced Options", value=ops, key=f"advanced_options_{step_number}"
    )
    if advanced_options:
        shots = st.number_input(
            "Shots (How many times to ask the agent)",
            min_value=1,
            value=1 if "shots" not in prompt else int(prompt["shots"]),
            key=f"shots_{step_number}",
        )
        context_results = st.number_input(
            "How many long term memories to inject (Default is 5)",
            min_value=1,
            value=5
            if "context_results" not in prompt
            else int(prompt["context_results"]),
            key=f"context_results_{step_number}",
        )
        browse_links = st.checkbox(
            "Enable Browsing Links in the user input",
            value=False if "browse_links" not in prompt else prompt["browse_links"],
            key=f"browse_links_{step_number}",
        )
        websearch = st.checkbox("Enable websearch")
        if websearch:
            websearch_depth = st.number_input(
                "Websearch depth",
                min_value=1,
                value=3,
                key=f"websearch_depth_{step_number}",
            )
        else:
            websearch_depth = 0
        if "disable_memory" not in prompt:
            enable_memory = st.checkbox(
                "Enable Memory Training (Any messages sent to and from the agent will be added to memory if enabled.)",
                value=False,
                key=f"enable_memory_{step_number}",
            )
        else:
            enable_memory = st.checkbox(
                "Enable Memory Training (Any messages sent to and from the agent will be added to memory if enabled.)",
                value=True if prompt["disable_memory"] == False else False,
                key=f"enable_memory_{step_number}",
            )
    else:
        shots = 1
        context_results = 5
        browse_links = False
        websearch = False
        websearch_depth = 0
        enable_memory = False
    return {
        "shots": shots,
        "context_results": context_results,
        "browse_links": browse_links,
        "websearch": websearch,
        "websearch_depth": websearch_depth,
        "disable_memory": (True if enable_memory == False else False),
    }


def prompt_selection(prompt: dict = {}, step_number: int = 0):
    prompt_categories = ApiClient.get_prompt_categories()
    prompt_category = st.selectbox(
        "Select Prompt Category",
        prompt_categories,
        index=prompt_categories.index("Default"),
        key=f"step_{step_number}_prompt_category",
    )
    available_prompts = ApiClient.get_prompts(prompt_category=prompt_category)
    try:
        custom_input_index = available_prompts.index("Custom Input")
    except:
        custom_input_index = 0
    prompt_name = st.selectbox(
        "Select Custom Prompt",
        available_prompts,
        index=available_prompts.index(prompt.get("prompt_name", "")) + 1
        if "prompt_name" in prompt
        else custom_input_index,
        key=f"step_{step_number}_prompt_name",
    )
    prompt_content = ApiClient.get_prompt(
        prompt_name=prompt_name, prompt_category=prompt_category
    )
    st.markdown(
        f"""
**Prompt Content**
```
{prompt_content}
```
        """
    )
    prompt_args_values = prompt_options(prompt=prompt, step_number=step_number)
    if prompt_name:
        prompt_args = ApiClient.get_prompt_args(
            prompt_name=prompt_name, prompt_category=prompt_category
        )
        args = build_args(args=prompt_args, prompt=prompt, step_number=step_number)
        new_prompt = {
            "prompt_name": prompt_name,
            "prompt_category": prompt_category,
            **args,
            **prompt_args_values,
        }
        return new_prompt


def command_selection(prompt: dict = {}, step_number: int = 0):
    agent_commands = cached_get_extensions()
    available_commands = []
    for commands in agent_commands:
        for command in commands["commands"]:
            available_commands.append(command["friendly_name"])

    command_name = st.selectbox(
        "Select Command",
        [""] + available_commands,
        key=f"command_name_{step_number}",
        index=available_commands.index(prompt.get("command_name", "")) + 1
        if "command_name" in prompt
        else 0,
    )

    if command_name:
        command_args = ApiClient.get_command_args(command_name=command_name)
        args = build_args(args=command_args, prompt=prompt, step_number=step_number)
        new_prompt = {
            "command_name": command_name,
            **args,
        }
        return new_prompt


def chain_selection(prompt: dict = {}, step_number: int = 0):
    available_chains = ApiClient.get_chains()
    chain_name = st.selectbox(
        "Select Chain",
        [""] + available_chains,
        index=available_chains.index(prompt.get("chain_name", "")) + 1
        if "chain" in prompt
        else 0,
        key=f"step_{step_number}_chain_name",
    )
    user_input = st.text_input(
        "User Input",
        value=prompt.get("input", ""),
        key=f"user_input_{step_number}",
    )

    if chain_name:
        new_prompt = {"chain": chain_name, "input": user_input}
        return new_prompt


def agent_selection(key: str = "select_learning_agent", heading: str = "Agent Name"):
    # Load the previously selected agent name
    try:
        with open(os.path.join("session.txt"), "r") as f:
            previously_selected_agent = f.read().strip()
    except FileNotFoundError:
        previously_selected_agent = None

    # Get the list of agent names
    agent_names = [agent["name"] for agent in ApiClient.get_agents()]

    # If the previously selected agent is in the list, use it as the default
    if previously_selected_agent in agent_names:
        default_index = (
            agent_names.index(previously_selected_agent) + 1
        )  # add 1 for the empty string at index 0
    else:
        default_index = 0

    # Create the selectbox
    selected_agent = st.selectbox(
        heading,
        options=[""] + agent_names,
        index=default_index,
        key=key,
    )
    if key == "select_learning_agent":
        # If the selected agent has changed, save the new selection
        if selected_agent != previously_selected_agent:
            with open(os.path.join("session.txt"), "w") as f:
                f.write(selected_agent)
            try:
                st.experimental_rerun()
            except Exception as e:
                logging.info(e)
    return selected_agent


def helper_agent_selection(
    current_agent: str, key: str = "select_learning_agent", heading: str = "Agent Name"
):
    # Get the list of agent names
    agent_names = [agent["name"] for agent in ApiClient.get_agents()]
    agent_config = ApiClient.get_agentconfig(agent_name=current_agent)
    agent_settings = agent_config.get("settings", {})
    helper_agent = agent_settings.get("helper_agent_name", current_agent)
    # Create the selectbox
    selected_agent = st.selectbox(
        heading,
        options=[""] + agent_names,
        index=agent_names.index(helper_agent) + 1,
        key=key,
    )
    return selected_agent


def conversation_selection(agent_name):
    if not os.path.exists("conversation.txt"):
        with open("conversation.txt", "w") as f:
            f.write("")
    try:
        with open(os.path.join("conversation.txt"), "r") as f:
            conversation = f.read().strip()
    except FileNotFoundError:
        conversation = ""
    conversations = ApiClient.get_conversations(
        agent_name=agent_name if agent_name else "OpenAI"
    )
    # New conversation checkbox
    with st.container():
        new_convo = st.checkbox("New Conversation", value=False)
        if len(conversations) == 0 or new_convo:
            conversation_name = st.text_input("Conversation Name", value="")
            if st.button("Create New Conversation"):
                ApiClient.new_conversation(
                    agent_name=agent_name if agent_name else "OpenAI",
                    conversation_name=conversation_name,
                )
                with open(os.path.join("conversation.txt"), "w") as f:
                    f.write(conversation_name)
                st.success(
                    "Conversation created successfully. Please uncheck 'New Conversation' to interact."
                )
                return conversation_name
        else:
            conversation_name = st.selectbox(
                "Choose a conversation",
                conversations,
                index=conversations.index(conversation)
                if conversation in conversations
                else 0,
            )
            if st.button("Delete Conversation"):
                ApiClient.delete_conversation(
                    agent_name=agent_name,
                    conversation_name=st.session_state["conversation"],
                )
                with open(os.path.join("conversation.txt"), "w") as f:
                    f.write("")
                st.success("Conversation history deleted successfully.")
                st.experimental_rerun()
            chat_history = get_history(
                agent_name=agent_name, conversation_name=conversation_name
            )

    if conversation != conversation_name:
        with open(os.path.join("conversation.txt"), "w") as f:
            f.write(conversation_name)
        st.experimental_rerun()
    return conversation_name
