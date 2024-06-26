import os
import json
import streamlit as st
from ApiClient import ApiClient
from components.selectors import (
    agent_selection,
    helper_agent_selection,
    prompt_selection,
    command_selection,
    chain_selection,
)
from components.docs import agixt_docs

st.set_page_config(
    page_title="Agent Management",
    page_icon=":hammer_and_wrench:",
    layout="wide",
)
agixt_docs()


@st.cache_data
def get_providers():
    return ApiClient.get_providers()


@st.cache_data
def get_tts_providers():
    return ApiClient.get_providers_by_service(service="tts")


@st.cache_data
def get_transcription_providers():
    return ApiClient.get_providers_by_service(service="transcription")


@st.cache_data
def get_translation_providers():
    return ApiClient.get_providers_by_service(service="translation")


@st.cache_data
def get_image_providers():
    return ApiClient.get_providers_by_service(service="image")


@st.cache_data
def get_vision_providers():
    return ApiClient.get_providers_by_service(service="vision")


@st.cache_data
def get_embeddings_providers():
    return ApiClient.get_providers_by_service(service="embeddings")


@st.cache_data
def provider_settings(provider_name: str):
    return ApiClient.get_provider_settings(provider_name=provider_name)


@st.cache_data
def get_extension_settings():
    return ApiClient.get_extension_settings()


@st.cache_data
def get_extensions():
    extensions = ApiClient.get_extensions()
    return [
        command["friendly_name"]
        for extension in extensions
        for command in extension["commands"]
    ]


providers = get_providers()
tts_providers = get_tts_providers()
transcription_providers = get_transcription_providers()
translation_providers = get_translation_providers()
image_providers = get_image_providers()
vision_providers = get_vision_providers()
embeddings_providers = get_embeddings_providers()
extension_setting_keys = get_extension_settings()


def render_provider_settings(agent_settings, provider_name: str):
    try:
        required_settings = provider_settings(provider_name=provider_name)
        # remove "provider" from required settings
        required_settings.pop("provider")
        # Get the values of the tts, image, embeddings, transcription, translation, and vision providers
        tts_provider = agent_settings.get("tts_provider", "default")
        image_provider = agent_settings.get("image_provider", "default")
        embeddings_provider = agent_settings.get("embeddings_provider", "default")
        transcription_provider = agent_settings.get("transcription_provider", "default")
        translation_provider = agent_settings.get("translation_provider", "default")
        vision_provider = agent_settings.get("vision_provider", "default")
        tts_settings = provider_settings(provider_name=tts_provider)
        tts_settings.pop("provider")
        image_settings = provider_settings(provider_name=image_provider)
        image_settings.pop("provider")
        embeddings_settings = provider_settings(provider_name=embeddings_provider)
        embeddings_settings.pop("provider")
        transcription_settings = provider_settings(provider_name=transcription_provider)
        transcription_settings.pop("provider")
        translation_settings = provider_settings(provider_name=translation_provider)
        translation_settings.pop("provider")
        vision_settings = provider_settings(provider_name=vision_provider)
        vision_settings.pop("provider")
        required_settings.update(tts_settings)
        required_settings.update(image_settings)
        required_settings.update(embeddings_settings)
        required_settings.update(transcription_settings)
        required_settings.update(translation_settings)
        required_settings.update(vision_settings)

    except (TypeError, ValueError):
        st.error(
            f"Error loading provider settings: expected a list or a dictionary, but got {required_settings}"
        )
        return {}
    rendered_settings = {}

    if not isinstance(required_settings, (list, dict)):
        st.error(
            f"Error loading provider settings: expected a list or a dictionary, but got {required_settings}"
        )
        return rendered_settings

    if isinstance(required_settings, dict):
        required_settings = list(required_settings.keys())

    for key in required_settings:
        if key in agent_settings:
            default_value = agent_settings[key]
        else:
            default_value = ""

        user_val = st.text_input(key, value=default_value)
        rendered_settings[key] = user_val
    return rendered_settings


def render_extension_settings(extension_settings, agent_settings):
    rendered_settings = {}

    for extension, settings in extension_settings.items():
        title_extension = extension.replace("_", " ").title()
        st.subheader(f"{title_extension} Settings")
        for key, val in settings.items():
            if key in agent_settings:
                default_value = agent_settings[key]
            else:
                default_value = val if val else ""
            if key.startswith("USE_") or key == "WORKING_DIRECTORY_RESTRICTED":
                user_val = st.checkbox(key, value=bool(default_value), key=key)
            else:
                user_val = st.text_input(
                    key, value=default_value, key=f"{extension}_{key}"
                )

            # Check if the user value exists before saving the setting
            if user_val:
                rendered_settings[key] = user_val
    return rendered_settings


st.header("Agent Management")
agent_name = agent_selection()

if "new_agent_name" not in st.session_state:
    st.session_state["new_agent_name"] = ""

# Add an input field for the new agent's name
new_agent = False

# Check if a new agent has been added and reset the session state variable
if (
    st.session_state["new_agent_name"]
    and st.session_state["new_agent_name"] != agent_name
):
    st.session_state["new_agent_name"] = ""

if not agent_name:
    agent_file = st.file_uploader("Import Agent", type=["json"])
    if agent_file:
        agent_name = agent_file.name.split(".json")[0]
        agent_settings = agent_file.read().decode("utf-8")
        agent_config = json.loads(agent_settings)
        ApiClient.import_agent(
            agent_name=agent_name,
            settings=agent_config["settings"],
            commands=agent_config["commands"],
        )
        st.success(f"Agent '{agent_name}' imported.")
    new_agent_name = st.text_input("New Agent Name")

    # Add an "Add Agent" button
    add_agent_button = st.button("Add Agent")

    # If the "Add Agent" button is clicked, create a new agent config file
    if add_agent_button:
        if new_agent_name:
            try:
                ApiClient.add_agent(new_agent_name, {})
                st.success(f"Agent '{new_agent_name}' added.")
                agent_name = new_agent_name
                with open(os.path.join("session.txt"), "w") as f:
                    f.write(agent_name)
                st.session_state["new_agent_name"] = agent_name
                st.rerun()  # Rerun the app to update the agent list
            except Exception as e:
                st.error(f"Error adding agent: {str(e)}")
        else:
            st.error("New agent name is required.")
    new_agent = True

if agent_name and not new_agent:
    # try:
    agent_config = ApiClient.get_agentconfig(agent_name=agent_name)
    export_button = st.download_button(
        "Export Agent Config",
        data=json.dumps(agent_config, indent=4),
        file_name=f"{agent_name}.json",
        mime="application/json",
    )
    agent_settings = agent_config.get("settings", {})
    if "mode" not in agent_settings:
        agent_settings["mode"] = "prompt"
    mode = st.selectbox(
        "Select Agent Chat Completions Mode",
        ["prompt", "command", "chain"],
        index=["prompt", "command", "chain"].index(agent_settings["mode"]),
        key="mode",
    )
    agent_settings["mode"] = mode
    if mode == "prompt":
        prompt_ops = prompt_selection(
            prompt={
                "prompt_name": (
                    agent_settings["prompt_name"]
                    if "prompt_name" in agent_settings
                    else "Chat"
                ),
                "prompt_category": (
                    agent_settings["prompt_category"]
                    if "prompt_category" in agent_settings
                    else "Default"
                ),
            }
        )
        agent_settings["prompt_name"] = prompt_ops["prompt_name"]
        agent_settings["prompt_category"] = prompt_ops["prompt_category"]
        agent_settings["prompt_args"] = prompt_ops
    elif mode == "command":
        command_ops = command_selection(
            prompt={
                "command_name": (
                    agent_settings["command_name"]
                    if "command_name" in agent_settings
                    else "Get Datetime"
                ),
                "command_args": (
                    agent_settings["command_args"]
                    if "command_args" in agent_settings
                    else {}
                ),
            }
        )
        agent_settings["command_name"] = command_ops["command_name"]
        agent_settings["command_args"] = command_ops["command_args"]
        if "command_variable" not in agent_settings:
            agent_settings["command_variable"] = ""
        command_variable = st.selectbox(
            "Select Command Variable",
            [""] + list(agent_settings["command_args"].keys()),
            index=(
                list(agent_settings["command_args"].keys()).index(
                    agent_settings["command_variable"]
                )
                + 1
                if agent_settings["command_variable"] in agent_settings["command_args"]
                else 0
            ),
            key="command_variable",
        )
        agent_settings["command_variable"] = command_variable
    elif mode == "chain":
        chain_ops = chain_selection(
            prompt={
                "chain_name": (
                    agent_settings["chain_name"]
                    if "chain_name" in agent_settings
                    else "Default Chain"
                ),
                "chain_args": (
                    agent_settings["chain_args"]
                    if "chain_args" in agent_settings
                    else {}
                ),
            }
        )
        agent_settings["chain_name"] = chain_ops["chain"]
        agent_settings["chain_args"] = chain_ops
    provider_name = agent_settings.get("provider", "")
    provider_name = st.selectbox(
        "Select LLM Provider",
        providers,
        index=providers.index(provider_name) if provider_name in providers else 0,
    )
    agent_settings["provider"] = provider_name
    embedding_provider = agent_settings.get("embeddings_provider", "default")
    embedding_provider = st.selectbox(
        "Select Embeddings Provider",
        embeddings_providers,
        index=(
            embeddings_providers.index(embedding_provider)
            if embedding_provider in embeddings_providers
            else 0
        ),
    )
    agent_settings["embeddings_provider"] = embedding_provider
    tts_provider = agent_settings.get("tts_provider", "default")
    tts_provider = st.selectbox(
        "Select TTS Provider",
        tts_providers,
        index=(
            tts_providers.index(tts_provider) if tts_provider in tts_providers else 0
        ),
    )
    agent_settings["tts_provider"] = tts_provider
    transcription_provider = agent_settings.get("transcription_provider", "default")
    transcription_provider = st.selectbox(
        "Select Transcription Provider",
        transcription_providers,
        index=(
            transcription_providers.index(transcription_provider)
            if transcription_provider in transcription_providers
            else 0
        ),
    )
    agent_settings["transcription_provider"] = transcription_provider
    translation_provider = agent_settings.get("translation_provider", "default")
    translation_provider = st.selectbox(
        "Select Translation Provider",
        translation_providers,
        index=(
            translation_providers.index(translation_provider)
            if translation_provider in translation_providers
            else 0
        ),
    )
    agent_settings["translation_provider"] = translation_provider
    vision_provider = agent_settings.get("vision_provider", "None")
    vision_providers = ["None"] + vision_providers
    vision_provider = st.selectbox(
        "Select Vision Provider",
        vision_providers,
        index=(
            vision_providers.index(vision_provider)
            if vision_provider in vision_providers
            else 0
        ),
    )
    agent_settings["vision_provider"] = vision_provider
    image_provider = agent_settings.get("image_provider", "None")
    image_providers = ["None"] + image_providers
    image_provider = st.selectbox(
        "Select Image Generation Provider",
        image_providers,
        index=(
            image_providers.index(image_provider)
            if image_provider in image_providers
            else 0
        ),
    )
    agent_settings["image_provider"] = image_provider

    with st.form(key="update_agent_settings_form"):
        st.subheader("Agent Settings")
        if "AUTONOMOUS_EXECUTION" not in agent_settings:
            agent_settings["AUTONOMOUS_EXECUTION"] = False
        autonomous_execution = st.checkbox(
            "Autonomous Execution (If checked, agent will run any enabled commands automatically, if not, it will create a chain of commands it would have executed.)",
            value=bool(agent_settings["AUTONOMOUS_EXECUTION"]),
            key="AUTONOMOUS_EXECUTION",
        )
        agent_settings["AUTONOMOUS_EXECUTION"] = autonomous_execution
        if "agent_helper_name" in agent_settings:
            agent_helper_name = agent_settings["helper_agent_name"]
        else:
            agent_helper_name = agent_name
        agent_settings["helper_agent_name"] = helper_agent_selection(
            current_agent=agent_name,
            key="select_helper_agent",
            heading="Select Helper Agent (Your agent will ask this one for help when it needs something.)",
        )
        if "WEBSEARCH_TIMEOUT" not in agent_settings:
            agent_settings["WEBSEARCH_TIMEOUT"] = 0
        websearch_timeout = st.number_input(
            "Websearch Timeout in seconds.  Set to 0 to disable the timeout and allow the AI to search until it feels it is done.",
            value=int(agent_settings["WEBSEARCH_TIMEOUT"]),
            key="WEBSEARCH_TIMEOUT",
        )
        st.subheader("Provider Settings")
        if provider_name:
            settings = render_provider_settings(
                agent_settings=agent_settings, provider_name=provider_name
            )
            agent_settings.update(settings)

        extension_settings = render_extension_settings(
            extension_settings=extension_setting_keys, agent_settings=agent_settings
        )

        # Update the extension settings in the agent_settings directly
        agent_settings.update(extension_settings)

        st.subheader("Agent Commands")
        # Fetch the available commands using the `Commands` class
        commands = get_extensions()
        available_commands = ApiClient.get_commands(agent_name=agent_name)
        for command in commands:
            if command not in available_commands:
                available_commands[command] = False

        # Save the existing command state to prevent duplication
        existing_command_states = {
            command_name: command_status
            for command_name, command_status in available_commands.items()
        }

        all_commands_selected = st.checkbox("Select All Commands")

        for command_name, command_status in available_commands.items():
            if all_commands_selected:
                available_commands[command_name] = True
            else:
                toggle_status = st.checkbox(
                    command_name,
                    value=command_status,
                    key=command_name,
                )
                available_commands[command_name] = toggle_status

        if st.form_submit_button("Update Agent Settings"):
            try:
                ApiClient.update_agent_commands(
                    agent_name=agent_name, commands=available_commands
                )
                ApiClient.update_agent_settings(
                    agent_name=agent_name, settings=agent_settings
                )
                st.success(f"Agent '{agent_name}' updated.")
            except Exception as e:
                st.error(f"Error updating agent: {str(e)}")
        if st.form_submit_button("Wipe Agent Memories"):
            try:
                ApiClient.wipe_agent_memories(agent_name=agent_name)
                st.success(f"Memories of agent '{agent_name}' wiped.")
            except Exception as e:
                st.error(f"Error wiping agent's memories: {str(e)}")

        if st.form_submit_button("Delete Agent"):
            try:
                ApiClient.delete_agent(agent_name=agent_name)
                st.success(f"Agent '{agent_name}' deleted.")
                st.session_state["new_agent_name"] = ""  # Reset the selected agent
                st.rerun()  # Rerun the app to update the agent list
            except Exception as e:
                st.error(f"Error deleting agent: {str(e)}")
    # except Exception as e:
    #    st.error(f"Error loading agent configuration: {str(e)}")

    # Trigger actions on form submit

else:
    st.error("Agent name is required.")
