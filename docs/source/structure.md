# Structure
This page wants to make the server architecture understandable (at least somewhen in the future)

## Text command from client

```{mermaid}
:zoom:
:caption: An already connected client sents a payload that contains text based commands
    flowchart BT
        Client --Websocket with payload--> ServerConsumer
        ServerConsumer --Extracted requests-->CommandExecutor
        ServerConsumer -. Can send messages to client browser ...-> Client
        id3 -.Can communicate with consumer..-> ServerConsumer
        subgraph APIServer
            id3[(ConsumerAPI)]
        end
        subgraph PluginManager
            CommandExecutor --> CommandParser
        end
        CommandExecutor <--Get consumer API--> APIServer
        subgraph ServerPluginTree
            direction BT
            CommandParser -- cmd and API obj --> id4(((Traverse plugin\ntree for cmd)))
            id4 -- not found in tree --> id5((End))
            id4 -- end node is plugin code --> id6((Execute node))
            id4 -- end node leads to dummy-->PluginDummy
    
        end
        subgraph TaskPool
            TaskQueue
            worker
        end
        PluginDummy <-- consumer UID--> id10[(PluginServerDatabase)]
        PluginDummy --yield-->PluginDummy
        %%PluginDummy -- RPC --> RemotePlugin
        PluginDummy -->TaskQueue
        worker --check for available tasks--> TaskQueue
        TaskQueue --return job -->worker
        worker -- RPC -->RemotePlugin
        %%RemotePlugin  -- Return ignored *--x PluginDummy
        RemotePlugin --For sending to client--> id3
```
* Calls with return are possible in plugin to plugin calls. In this case they will be discarded
Edit helper: https://mermaid-js.github.io/mermaid-live-editor/