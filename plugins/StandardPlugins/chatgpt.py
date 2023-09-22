import asyncio
import openai
from plugins.api import *
import logging
import json
import asyncio
from pprint import pp
from django.conf import settings
# from asgiref.sync import
logger = logging.getLogger("ChatGPT")

config = {"temperature": 0.3, "model": "gpt-3.5-turbo", "system_string":
    r"""You are PIXI an acronym for: Personal Interactive eXplainable Intelligence
You are part of an interactive XAI website (called RIXA for Real tIme eXplainable Ai) analyzer that features you and left to you place for plots and similar.
You respond to requests either by text or by using one of the functions provided to you.
Should a requested function be unavailable you should inform the user e.g. the user asks: "Can you show me a histogram for X"?
and you are unable to provide a histogram then answer with something like "I am sorry I can't draw histograms."
However if you have an alternative that is somewhat fitting, offer it to the user.

Enclose every math expression NO MATTER HOW SMALL in double dollar signs like e.g. $$x^2$$!
""", "enable_function_calls": True, "use_embeddings": False}


# Currently you are in the first iteration of RIXA. Many features are untested and unfinished.
# Sometimes the developer, Finn, will identify himself. Then you should refrain from nice and wordy formulations and give straight technical answers.
# Also the actual content of answers or function calls is mostly irrelevant to him. Really important are the internal mechanisms.

@plugin_init(name="chatgpt", is_local=True, config=config,
             plugin_type=PluginType.NL_INFERENCE, hidden_in_function_dic=True)
def chatgpt(self, config, meta_config):
    api_key = settings.OPENAI_API_KEY
    if not api_key or api_key == "NONE":
        logger.error("API key for OpenAI not set!")
        settings.NLP_BACKEND = "none"
        return

    openai.api_key = api_key
    self.model = config["model"]
    self.temperature_value = config["temperature"]


@chatgpt.api_init()
def setup_conv_tracker(uid, scope):
    if "conversations" not in scope["session"]:
        start_msgs = [{"role": "system", "content": chatgpt.config["system_string"]}]
        # if "example_conv" in chatgpt.config and chatgpt.config["example_conv"]:
        #     start_msgs += chatgpt.config["example_conv"]
        # start_msgs.append({"role":"server","metadata":{"display_only": True}, "content":settings.NLP_GREETING})
        start_msgs.append({"role": "assistant", "content": "Hello, I am PIXI. Currently I can assist with exploration of a coronary heart disease dataset."})
        # settings.NLP_GREETING
        scope["session"]["conversations"] = {"active_id": "0",
                                             "available": {"0": {"active_msg_id": 1,
                                                               "messages": start_msgs}}}


@chatgpt.plugin_method()
@argument("switch", type=bool)
async def enable_function_call(api, switch):
    # DONT DO THIS.
    # This should be a per user setting but I needed something quick. There will be user configs at some point
    chatgpt.config["enable_function_calls"] = switch
    await api.display_in_chat(f"Enable functions set to: {switch}")


@chatgpt.plugin_method()
async def get_answer(api, client_payload):
    await api.send_flag(MessageFlags.LONG_CALL_STARTED)
    await api.add_to_conv_tracker(client_payload["content"], "user")
    conv_tracker = await api.get_conv_tracker(exlude_key="display_only")

    corpus = ""
    if chatgpt.config["use_embeddings"] and is_plugin_available("text_retriever"):
        corpus = await api.call_plugin_function("text_retriever", "retrieve_text", args=(client_payload["content"],),
                                                kwargs={"as_string": True})
        if not corpus:
            await api.display_message("This is really bad",  5, MessageLevel.DANGER)
        conv_tracker[-1]["content"] = "##CONTEXT##" + corpus + "####\n" +conv_tracker[-1]["content"]
    try:

        if chatgpt.config["enable_function_calls"]:
            kwargs = {"model": chatgpt.ctx.model,
                      "messages": conv_tracker,
                      "temperature": chatgpt.ctx.temperature_value,
                      "function_call": "auto",
                      "functions": plugin_conf.all_available_functions
                      }

        else:
            kwargs = {"model": chatgpt.ctx.model,
                      "messages": conv_tracker,
                      "temperature": chatgpt.ctx.temperature_value,
                      }
        with_kwargs = functools.partial(openai.ChatCompletion.create, **kwargs)
        response = await plugin_conf.async_loop.run_in_executor(None, with_kwargs)

        # response = {"choices":[{"message":{"content":"yo"}, "finish_reason":"message"}], "usage":{"completion_tokens":3,"prompt_tokens":4}}
    except Exception as e:
        await api.remove_last_conv_entry()
        raise e
    if response["choices"][0]["finish_reason"] == "function_call":

        msg = response["choices"][0]["message"]["function_call"]
        # print(msg)
        func_name = msg["name"]
        func_name_call = func_name.replace("-", "_")
        kwargs = json.loads(msg["arguments"])

        found_entry = None
        for entry in plugin_conf.all_available_functions:
            if entry['name'] == func_name:
                found_entry = entry
                break
        if not found_entry:
            api.show_message(f"{func_name} not existing. Request cancelled!", theme="danger")
            return
        ret_vals = await api.call_plugin_function(function_name=func_name_call, kwargs=kwargs)


        param_desc = found_entry["parameters"]["properties"]
        params_chosen = response["choices"][0]["message"]["function_call"]["arguments"]

        content = f"Description: {found_entry['description']}\nArgument description: {param_desc}\n" \
                  f"Used arguments: {params_chosen}\nReturn vals: {ret_vals}"
        # print(content)

        await api.add_to_conv_tracker(content, "function", add_keys={"name":func_name})
        conv_tracker = await api.get_conv_tracker(exlude_key="display_only")

        kwargs = {"model": chatgpt.ctx.model,
                  "messages": conv_tracker,
                  "temperature": chatgpt.ctx.temperature_value,
                  }
        with_kwargs = functools.partial(openai.ChatCompletion.create, **kwargs)
        response = await plugin_conf.async_loop.run_in_executor(None, with_kwargs)
        # print(response)

    ret_msg = response["choices"][0]["message"]["content"]
    completion_tokens = response["usage"]["completion_tokens"]
    prompt_tokens = response["usage"]["prompt_tokens"]
    metadata = {"completion_tokens": completion_tokens, "prompt_tokens": prompt_tokens, "cost": (
                  0.0015 * prompt_tokens + 0.002 * completion_tokens) / 1000}
    client_meta = dict(metadata)
    client_meta["context"] = corpus
    ret_msg = await api.add_to_conv_tracker(ret_msg, "assistant", client_meta)
    await api.sync_session_storage_db()
    await api.display_in_chat(text=ret_msg)

        # await api.display_in_chat(ret_msg["content"], role=ret_msg["role"], metadata=ret_msg["metadata"])
