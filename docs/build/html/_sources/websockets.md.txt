# WebSocket Communication

This document outlines how use ajax requests to communicate with the server via WebSocket.


## Available Commands

### 1. execute_plugin_code

Executes plugin code on the server. Typically, initiated by the user for debugging and not for UI purposes.
Use call_plugin_function for programmatic access to plugin functions.

This command requires the code to be enclosed in #s.

**Parameters:**
- `type`: "execute_plugin_code"
- `content`: The code to be executed

**Example:**
```json
{
    "type": "execute_plugin_code",
    "content": "##help()#"
}
```

### 2. call_plugin_function

Initiates a call for a plugin function on the server.
Can be used for programmatic access to plugin functions e.g. a UI element that triggers a plugin function.

```{warning}
Pay attention on how you allow usage. If a chat message is being processed, most likely RIXA will ignore a function call.
Rate limits apply to function calls as well.
```

**Parameters:**
- `type`: "call_plugin_function"
- `function_name`: The name of the function to be called
- `args`: (Optional) List of positional arguments
- `kwargs`: (Optional) Dictionary of keyword arguments

**Example:**
```json
{
    "type": "call_plugin_function",
    "function_name": "my_function",
    "args": ["arg1", "arg2"],
    "kwargs": {"key1": "value1", "key2": "value2"}
}
```

### 3. usr_msg
```{warning}
Custom UI elements should not use this!
Messages outside the usual conversation cycle will be ignored
```
Sends a user message to the server for processing.

**Parameters:**
- `type`: "usr_msg"
- `content`: The user's message content

**Example:**
```json
{
    "type": "usr_msg",
    "content": "What's the weather like today?"
}
```

### 4. change_setting

Changes a user-specific setting on the server.

**Parameters:**
- `type`: "change_setting"
- `setting`: The name of the setting to change
- `value`: The new value for the setting

**Supported Settings:**
- `enable_function_calls`
- `enable_knowledge_retrieval`
- `selected_chat_mode`

**Example:**
```json
{
    "type": "change_setting",
    "setting": "enable_function_calls",
    "value": true
}
```

### 5. update_plugin_setting

Updates a specific plugin setting for the user.

**Parameters:**
- `type`: "update_plugin_setting"
- `plugin_id`: The ID of the plugin
- `setting_id`: The ID of the setting within the plugin
- `value`: The new value for the setting

**Example:**
```json
{
    "type": "update_plugin_setting",
    "plugin_id": "my_plugin",
    "setting_id": "api_key",
    "value": "new_api_key_value"
}
```

### 6. bug_report

Submits a bug report to the server.

**Parameters:**
- `type`: "bug_report"
- `report`: The text content of the bug report
- `image`: (Optional) Base64 encoded image related to the bug

**Example:**
```json
{
    "type": "bug_report",
    "report": "I encountered an error when trying to...",
    "image": "data:image/png;base64,iVBORw0KGgoAAAAN..."
}
```

### 7. delete_current_tracker

Deletes the current conversation tracker and starts a new chat.

**Parameters:**
- `type`: "delete_current_tracker"

**Example:**
```json
{
    "type": "delete_current_tracker"
}
```

### 8. get_chat_modes

Retrieves available chat modes for the current user.

**Parameters:**
- `type`: "get_chat_modes"

**Example:**
```json
{
    "type": "get_chat_modes"
}
```

### 9. get_plugin_settings

Retrieves all plugin settings, including global and user-specific values.
User specific values override global values.

**Parameters:**
- `type`: "get_plugin_settings"

**Example:**
```json
{
    "type": "get_plugin_settings"
}
```

### 10. user_settings

Retrieves user-specific settings unrelated to any specific plugin e.g. the selected chat mode.

**Parameters:**
- `type`: "user_settings"

**Example:**
```json
{
    "type": "user_settings"
}
```

### 11. get_utilization_info

Retrieves server utilization information.

**Parameters:**
- `type`: "get_utilization_info"

**Example:**
```json
{
    "type": "get_utilization_info"
}
```

### 12. get_global_settings

Retrieves global server settings e.g. the currently set website title.

**Parameters:**
- `type`: "get_global_settings"

**Example:**
```json
{
    "type": "get_global_settings"
}
```

### 13. get_chat_start_info

Retrieves chat start information for a specific chat mode.
Used for initializing a new chat mode. This includes
- The chats title
- Custom UI elements
- Onboarding messages

**Parameters:**
- `type`: "get_chat_start_info"
- `selected_chat_mode`: The chat mode to retrieve information for

**Example:**
```json
{
    "type": "get_chat_start_info",
    "selected_chat_mode": "default"
}
```

## Server Responses

The server will respond to these commands with JSON messages. The structure of the response will depend on the specific command, but generally, it will include:

- `role`: Indicates the type of response (e.g., "chat_modes", "plugin_settings", "user_settings", etc.)
- `content`: The actual content of the response

## Error Handling

Errors will be returned via a message in the format
    
```json
{
    "type": "status",
    "level": "error",
    "content": "Error message here"
}
```

These are meant to be displayed to the user. Silent messaging should be done via logging inside the plugins or the server.
