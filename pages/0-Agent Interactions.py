import streamlit as st
import os
from components.selectors import (
    agent_selection,
    conversation_selection,
    skip_args,
    prompt_options,
    prompt_selection,
)
from ApiClient import ApiClient
from components.docs import agixt_docs, predefined_injection_variables

st.set_page_config(
    page_title="Agent Interactions",
    page_icon=":speech_balloon:",
    layout="wide",
)

agixt_docs()

st.header("Agent Interactions")
show_injection_var_docs = st.checkbox("Show Prompt Injection Variable Documentation")
if show_injection_var_docs:
    predefined_injection_variables()
try:
    with open(os.path.join("session.txt"), "r") as f:
        agent_name = f.read().strip()
except:
    agent_name = "OpenAI"
st.session_state["conversation"] = conversation_selection(agent_name=agent_name)
mode = st.selectbox("Select Mode", ["Chat", "Chains", "Prompt", "Instruct"])
agent_name = agent_selection() if mode != "Chains" else None
prompt_name = "Chat" if mode != "Instruct" else "instruct"

if mode != "Chains":
    if mode != "Prompt":
        prompt_args_values = prompt_options(prompt={})
        user_input = st.text_area("User Input")
    else:
        prompt_arg_values = prompt_selection()

    if st.button("Send"):
        prompt_args_values["conversation_name"] = st.session_state["conversation"]
        with st.spinner("Thinking, please wait..."):
            response = ApiClient.prompt_agent(
                agent_name=agent_name,
                prompt_name=prompt_name,
                prompt_args=prompt_args_values,
            )
            if response:
                st.experimental_rerun()
else:
    chain_names = ApiClient.get_chains()
    chain_name = st.selectbox("Select a Chain to Run", chain_names)
    agent_override = st.checkbox("Override Agent")
    if agent_override:
        agent_name = agent_selection()
    else:
        agent_name = ""
    advanced_options = st.checkbox("Show Advanced Options")
    if advanced_options:
        single_step = st.checkbox("Run a Single Step")
        if single_step:
            from_step = st.number_input("Step Number to Run", min_value=1, value=1)
            all_responses = False
            if st.button("Run Chain Step"):
                if chain_name:
                    responses = ApiClient.run_chain_step(
                        chain_name=chain_name,
                        user_input=user_input,
                        agent_name=agent_name,
                        step_number=from_step,
                        chain_args=args,
                    )
                    st.success(f"Chain '{chain_name}' executed.")
                    st.write(responses)
                else:
                    st.error("Chain name is required.")
        else:
            from_step = st.number_input("Start from Step", min_value=1, value=1)
            all_responses = st.checkbox(
                "Show All Responses (If not checked, you will only be shown the last step's response in the chain when done.)"
            )
    user_input = st.text_area("User Input")
    args = {}
    if chain_name:
        chain_args = ApiClient.get_chain_args(chain_name=chain_name)
        for arg in chain_args:
            if arg not in skip_args and arg != "user_input":
                override_arg = st.checkbox(f"Override `{arg}` argument.")
                if override_arg:
                    args[arg] = st.text_area(arg)
    if args != {}:
        args_copy = args.copy()
        for arg in args_copy:
            if args[arg] == "":
                del args[arg]
    args["conversation_name"] = st.session_state["conversation"]

    if st.button("Run Chain"):
        if chain_name:
            responses = ApiClient.run_chain(
                chain_name=chain_name,
                user_input=user_input,
                agent_name=agent_name,
                all_responses=all_responses,
                from_step=from_step,
                chain_args=args,
            )
            st.success(f"Chain '{chain_name}' executed.")
            st.write(responses)
        else:
            st.error("Chain name is required.")
