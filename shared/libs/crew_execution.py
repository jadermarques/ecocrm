
import logging
import json
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from langchain.callbacks.base import BaseCallbackHandler

# Setup Shared Logging for Executions
LOG_DIR = Path("/app/data/logs") # Standardized path for container
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("crew_execution")
if not logger.handlers:
    # Basic setup if not already configured by main app
    logging.basicConfig(level=logging.INFO)

# Portuguese Prompts
AGENT_SYSTEM_TEMPLATE_PT = """Você é {role}. {backstory}
Seu objetivo pessoal é: {goal}
Você SÓ deve usar as ferramentas listadas abaixo e NUNCA inventar ferramentas que não estão listadas:

{tools}

Use o seguinte formato:

Thought: você deve sempre pensar sobre o que fazer
Action: a ação a ser tomada, apenas um nome de [{tool_names}], exatamente como está escrito.
Action Input: a entrada para a ação, apenas um dicionário python simples, entre chaves, usando " para envolver chaves e valores.
Observation: o resultado da ação

Quando tiver todas as informações necessárias:

Thought: Agora eu sei a resposta final
Final Answer: a resposta final para a pergunta original de entrada

Tarefas Atuais: {input}

Comece! Isso é MUITO importante para você, use as ferramentas disponíveis e dê sua melhor Resposta Final, seu trabalho depende disso!


Thought:
"""

AGENT_PROMPT_TEMPLATE_PT = """
Tarefa Atual: {input}

Você DEVE retornar o conteúdo completo real como a resposta final, não um resumo, e em PORTUGUÊS DO BRASIL.

Comece! Isso é MUITO importante para você, use as ferramentas disponíveis e dê sua melhor Resposta Final, seu trabalho depende disso!


Thought:
"""

AGENT_RESPONSE_TEMPLATE_PT = """
{{ .Response }}
"""

def create_version_logger(version_tag: str) -> logging.Logger:
    """
    Cria um logger específico para uma versão da crew.
    Logs são salvos em formato legível em português.
    """
    # Remove o prefixo 'v' se existir para o nome do arquivo
    clean_tag = version_tag.replace('v', '').replace('V', '')
    version_log_file = LOG_DIR / f"v{clean_tag}.log"
    
    # Cria logger específico para a versão
    version_logger = logging.getLogger(f"crew_v{clean_tag}")
    version_logger.setLevel(logging.DEBUG)
    
    # Check if handlers already exist to avoid duplication
    if not version_logger.handlers:
        # File handler para esta versão
        version_fh = logging.FileHandler(version_log_file, encoding='utf-8')
        version_fh.setLevel(logging.DEBUG)
        
        # Formato mais legível em português
        version_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )
        version_fh.setFormatter(version_formatter)
        version_logger.addHandler(version_fh)
    
    return version_logger

class CrewCallbackHandler(BaseCallbackHandler):
    """Handler LangChain para logs detalhados em português"""
    
    def __init__(self, version_logger: logging.Logger, agent_name: str = "Agente"):
        super().__init__()
        self.version_logger = version_logger
        self.agent_name = agent_name
        self.llm_calls = 0
        
    def on_chain_start(self, serialized, inputs, **kwargs):
        """Captura início de chains (incluindo inputs/contexto recebido)"""
        chain_name = serialized.get("name", "Unknown Chain") if isinstance(serialized, dict) else str(serialized)
        # Filtra chains internas irrelevantes para manter o log limpo
        if "AgentExecutor" in chain_name or "Crew" in chain_name:
            self.version_logger.info(f"📥 ENTRADA RECEBIDA - {self.agent_name} (CONTEXTO/INPUT)")
            # Loga inputs de forma limpa
            input_str = str(inputs.get('input', inputs))
            if len(input_str) > 500:
                self.version_logger.info(f"   {input_str[:500]}... (truncado)")
            else:
                self.version_logger.info(f"   {input_str}")
            self.version_logger.info("")

    def on_llm_start(self, serialized, prompts, **kwargs):
        """Captura o início de chamadas LLM"""
        self.llm_calls += 1
        model_name = serialized.get("name", "Unknown") if isinstance(serialized, dict) else str(serialized)
        
        self.version_logger.info("="*80)
        self.version_logger.info(f"🤖 CHAMADA LLM #{self.llm_calls} - {self.agent_name}")
        self.version_logger.info(f"   ├─ Modelo: {model_name}")
        self.version_logger.info("")
        
        for idx, prompt in enumerate(prompts):
            self.version_logger.info(f"   📝 PROMPT #{idx+1}:")
            lines = prompt.split('\n')
            for line in lines[:50]:
                self.version_logger.info(f"      {line}")
            if len(lines) > 50:
                self.version_logger.info(f"      ... (+{len(lines)-50} linhas)")
            self.version_logger.info("")
    
    def on_llm_end(self, response, **kwargs):
        """Captura a resposta da LLM"""
        if hasattr(response, 'generations') and response.generations:
            if response.generations[0]:
                text = response.generations[0][0].text
                self.version_logger.info(f"✅ RESPOSTA DA LLM #{self.llm_calls}:")
                
                lines = text.split('\n')
                for line in lines[:100]:
                    self.version_logger.info(f"      {line}")
                if len(lines) > 100:
                    self.version_logger.info(f"      ... (+{len(lines)-100} linhas)")
                self.version_logger.info("")
                self.version_logger.info("="*80)
                self.version_logger.info("")
    
    def on_llm_error(self, error, **kwargs):
        """Captura erros da LLM"""
        self.version_logger.error(f"❌ ERRO NA LLM #{self.llm_calls}: {str(error)}")
        self.version_logger.info("")
    
    def on_agent_action(self, action, **kwargs):
        """Captura ações do agente, focando em raciocínio e delegação"""
        self.version_logger.info(f"🎯 AÇÃO DO AGENTE")
        
        # Extrair pensamento/raciocínio do log
        thought = ""
        if hasattr(action, 'log') and action.log:
            # Tenta pegar apenas a parte "Thought:"
            parts = action.log.split('Action:')
            thought_part = parts[0].replace('Thought:', '').strip()
            if thought_part:
                thought = thought_part
            else:
                thought = action.log[:500] # Fallback
        
        if thought:
            self.version_logger.info(f"   💭 Raciocínio (O que ele pensou):")
            self.version_logger.info(f"      {thought}")
            self.version_logger.info("")

        # Tratamento especial para delegação
        tool_name = action.tool.lower()
        if "delegate" in tool_name or "coworker" in tool_name:
             self.version_logger.info(f"   🤝 DELEGAÇÃO / ENVIO PARA OUTRO AGENTE")
             self.version_logger.info(f"      Ferramenta: {action.tool}")
             
             # Tenta extrair motivos e contexto dos inputs
             tool_input = action.tool_input
             if isinstance(tool_input, str):
                 try:
                     tool_input = json.loads(tool_input)
                 except:
                     pass
             
             if isinstance(tool_input, dict):
                 coworker = tool_input.get('coworker', tool_input.get('agent', 'Desconhecido'))
                 task = tool_input.get('task', tool_input.get('question', ''))
                 context = tool_input.get('context', '')
                 
                 self.version_logger.info(f"      👉 Para Agente: {coworker}")
                 self.version_logger.info(f"      📝 Tarefa Designada: {task}")
                 if context:
                     self.version_logger.info(f"      📄 Contexto/Motivo Enviado: {context}")
             else:
                 self.version_logger.info(f"      Input: {tool_input}")
        
        else:
            # Log de ferramenta normal
            self.version_logger.info(f"   🔧 Ferramenta Escolhida: {action.tool}")
            self.version_logger.info(f"      Input: {str(action.tool_input)[:500]}")
            
        self.version_logger.info("")
    
    def on_agent_finish(self, finish, **kwargs):
        """Captura conclusão do agente"""
        self.version_logger.info(f"🏁 AGENTE FINALIZOU (RESPOSTA FINAL)")
        output = str(finish.return_values.get('output', finish.return_values)) if isinstance(finish.return_values, dict) else str(finish.return_values)
        self.version_logger.info(f"   Output: {output[:500]}...")
        if len(output) > 500:
            self.version_logger.info(f"   ... (truncado)")
        self.version_logger.info("")

async def execute_crew_from_snapshot(snapshot: dict, inputs: dict, version_tag: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a crew based on the version snapshot using the installed crewai package.
    Returns a dict with 'response' and 'agent_name'.
    """
    logger.info("="*80)
    logger.info("Starting crew execution (Shared Lib)")
    logger.info(f"Inputs received: {inputs}")
    # avoid excessively large log
    # logger.info(f"Snapshot received: {json.dumps(snapshot, indent=2)}")
    
    # Cria logger específico para a versão se fornecido
    version_logger = None
    if version_tag:
        version_logger = create_version_logger(version_tag)
        
        version_logger.info("="*80)
        version_logger.info(f"🚀 INÍCIO DA EXECUÇÃO DA CREW - Versão {version_tag}")
        version_logger.info("="*80)
        version_logger.info("📥 INPUT RECEBIDO:")
        for key, value in inputs.items():
            version_logger.info(f"   ├─ {key}: {value}")
        version_logger.info("")
    
    try:
        from crewai import Agent, Task, Crew, Process
        # from langchain.callbacks.base import BaseCallbackHandler
        logger.info("✓ CrewAI imports successful")
        
        if version_logger:
            version_logger.info("✅ Módulos do CrewAI importados com sucesso")
            version_logger.info("")
        
        # 1. Reconstruct Agents
        agents_map = {}
        agents = []
        
        snapshot_agents = snapshot.get('agents', [])
        logger.info(f"Processing {len(snapshot_agents)} agents from snapshot")
        
        if version_logger and snapshot_agents:
            version_logger.info(f"👥 RECONSTRUINDO {len(snapshot_agents)} AGENTE(S) DO SNAPSHOT")
            version_logger.info("")
        
        for idx, agent_data in enumerate(snapshot_agents):
            # logger.debug(f"Agent {idx+1}/{len(snapshot_agents)}: {json.dumps(agent_data, indent=2)}")
            
            if version_logger:
                version_logger.info(f"🔨 Agente #{idx+1}: {agent_data['name']}")
                version_logger.info(f"   ├─ Role: {agent_data['role']}")
                version_logger.info(f"   ├─ Goal: {agent_data['goal']}")
                backstory_preview = agent_data.get('backstory', 'An AI agent in the crew.')[:150]
                version_logger.info(f"   ├─ Backstory: {backstory_preview}...")
                version_logger.info(f"   ├─ LLM: Padrão do sistema (ChatOpenAI via env) ou {agent_data.get('llm')}")
                version_logger.info(f"   └─ Ferramentas: {len(agent_data.get('tools', []))}")
                version_logger.info("")
            
            # Create LLM with callback for logging
            # INSTANTIATE HANDLER FOR THIS AGENT
            this_agent_handler = None
            if version_logger:
                this_agent_handler = CrewCallbackHandler(version_logger, agent_name=agent_data['name'])

            from langchain_openai import ChatOpenAI
            
            model_name = agent_data.get('llm')
            if not model_name: 
                 model_name = 'gpt-4o-mini'

            agent_llm = ChatOpenAI(
                model=model_name,
                temperature=0.7,
                callbacks=[this_agent_handler] if this_agent_handler else [],
                verbose=True
            )
            
            agent = Agent(
                role=agent_data['role'],
                goal=agent_data['goal'],
                backstory=agent_data.get('backstory', 'An AI agent in the crew.') + "\n\nIMPORTANTE: Todo o seu raciocínio (Thought) e suas respostas finais DEVEM ser em PORTUGUÊS DO BRASIL. Mesmo que as instruções do sistema sejam em inglês, mantenha seu processo de pensamento em português.",
                verbose=agent_data.get('verbose', True),
                allow_delegation=agent_data.get('allow_delegation', True),
                llm=agent_llm,
                max_iter=agent_data.get('max_iter', 20),
                max_rpm=agent_data.get('max_rpm')
            )
            # Inject Portuguese Template
            agent.system_template = AGENT_SYSTEM_TEMPLATE_PT
            agent.prompt_template = AGENT_PROMPT_TEMPLATE_PT
            agent.response_template = AGENT_RESPONSE_TEMPLATE_PT
            agents_map[agent_data['id']] = agent
            agents.append(agent)
            logger.info(f"✓ Created agent '{agent_data['role']}' (ID: {agent_data['id']})")
            
        logger.info(f"Total agents created: {len(agents)}")
        
        # 2. Reconstruct Tasks
        tasks = []
        snapshot_tasks = snapshot.get('tasks', [])
        logger.info(f"Processing {len(snapshot_tasks)} tasks from snapshot")
        
        if version_logger and snapshot_tasks:
            version_logger.info(f"📋 RECONSTRUINDO {len(snapshot_tasks)} TAREFA(S) DO SNAPSHOT")
            version_logger.info("")
        
        # Need to handle Context correctly if tasks depend on each other.
        # CrewAI expects 'context' in Task to be a list of Task objects.
        # Map task_id from snapshot -> Task Object
        snapshot_task_id_to_obj = {}

        for idx, task_data in enumerate(snapshot_tasks):
            # logger.debug(f"Task {idx+1}/{len(snapshot_tasks)}: {json.dumps(task_data, indent=2)}")
            
            agent_id = task_data.get('agent_id')
            agent = agents_map.get(agent_id)
            
            if not agent:
                logger.warning(f"⚠ Task '{task_data.get('name')}' has invalid agent_id {agent_id}, skipping")
                continue
            
            # Get agent role for logging
            agent_role = next((a['role'] for a in snapshot_agents if a['id'] == agent_id), "Unknown")
            
            if version_logger:
                version_logger.info(f"📝 Tarefa #{idx+1}: {task_data.get('name')}")
                version_logger.info(f"   ├─ Agente Responsável: {agent_role} (ID: {agent_id})")
                desc_preview = task_data['description'][:200]
                version_logger.info(f"   ├─ Descrição: {desc_preview}...")
                output_preview = task_data['expected_output'][:150]
                version_logger.info(f"   └─ Output Esperado: {output_preview}...")
                version_logger.info("")
            
            # Append expected_output to description so it's visible in the prompt since we removed it from the system template
            full_description = task_data['description']
            if task_data.get('expected_output'):
                full_description += f"\n\nCritérios de Saída Esperados: {task_data['expected_output']}"
            
            task = Task(
                description=full_description,
                expected_output=task_data['expected_output'],
                agent=agent,
                async_execution=task_data.get('async_execution', False)
            )
            tasks.append(task)
            snapshot_task_id_to_obj[task_data['id']] = task
            logger.info(f"✓ Created task '{task_data.get('name')}' for agent {agent_id}")
        
        # Retroactive Context Assignment
        # Now that all tasks are created, we can assign context based on context_task_ids
        for task_data in snapshot_tasks:
             context_ids = task_data.get('context_task_ids', [])
             if context_ids:
                 task_obj = snapshot_task_id_to_obj.get(task_data['id'])
                 context_tasks = [snapshot_task_id_to_obj[cid] for cid in context_ids if cid in snapshot_task_id_to_obj]
                 if task_obj and context_tasks:
                     task_obj.context = context_tasks
                     logger.info(f"   -> Assigned context for task {task_data['id']}: {[t.description[:20] for t in context_tasks]}")

        logger.info(f"Total tasks created: {len(tasks)}")
        
        # 3. Create Crew
        crew_config = snapshot.get('crew', {})
        logger.info(f"Crew config: {json.dumps(crew_config, indent=2)}")
        
        process_type = Process.hierarchical if crew_config.get('process') == 'hierarchical' else Process.sequential
        logger.info(f"Process type: {process_type}")
        
        # Build crew kwargs
        crew_kwargs = {
            'agents': agents,
            'tasks': tasks,
            'verbose': True, # framework side verbose
            'process': process_type,
            'memory': crew_config.get('memory_enabled', False),
            'max_rpm': crew_config.get('max_rpm')
        }
        
        # Add manager_llm for hierarchical process
        if process_type == Process.hierarchical:
            from langchain_openai import ChatOpenAI
            
            manager_llm_name = crew_config.get('manager_llm')
            if not manager_llm_name:
                manager_llm_name = 'gpt-4o-mini'  # Default fallback
                logger.warning(f"⚠ No manager_llm in config, using fallback: {manager_llm_name}")
            else:
                logger.info(f"Using manager_llm from config: {manager_llm_name}")
            
            # Create Handler for Manager
            manager_handler = None
            if version_logger:
                manager_handler = CrewCallbackHandler(version_logger, agent_name="Gerente da Equipe")

            # Create ChatOpenAI instance with callback
            manager_llm_instance = ChatOpenAI(
                model=manager_llm_name, 
                temperature=0.7,
                callbacks=[manager_handler] if manager_handler else [],
                verbose=True
            )
            
            # Create Explicit Manager Agent for Portuguese logs
            manager_agent = Agent(
                role="Gerente da Equipe",
                goal="Gerenciar a equipe para completar as tarefas de forma eficiente e em Português.",
                backstory="Você é um gerente experiente e eficaz. IMPORTANTE: Todo o seu raciocínio (Thought) e suas decisões devem ser pensadas e explicadas em PORTUGUÊS DO BRASIL.",
                llm=manager_llm_instance,
                allow_delegation=True,
                verbose=True
            )
            # Inject Portuguese Template
            manager_agent.system_template = AGENT_SYSTEM_TEMPLATE_PT
            manager_agent.prompt_template = AGENT_PROMPT_TEMPLATE_PT
            manager_agent.response_template = AGENT_RESPONSE_TEMPLATE_PT
            crew_kwargs['manager_agent'] = manager_agent
        
        logger.info(f"Crew kwargs prepared: agents={len(crew_kwargs['agents'])}, tasks={len(crew_kwargs['tasks'])}, process={crew_kwargs['process']}, manager={crew_kwargs.get('manager_agent', 'N/A')}")
        
        # Validate before creating Crew
        if not crew_kwargs['agents']:
            error_msg = "❌ ERROR: No agents to create crew! Check snapshot data."
            logger.error(error_msg)
            return {"response": error_msg, "agent_name": "System"}
            
        if not crew_kwargs['tasks']:
            error_msg = "❌ ERROR: No tasks to create crew! Check snapshot data."
            logger.error(error_msg)
            return {"response": error_msg, "agent_name": "System"}
        
        logger.info("Creating Crew instance...")
        crew = Crew(**crew_kwargs)
        logger.info("✓ Crew instance created successfully")
        
        # 4. Kickoff
        logger.info(f"Starting crew kickoff with inputs: {inputs}")
        
        # For compatibility, handle event loops if called from async context
        # CrewAI .kickoff() is synchronous (blocking) but uses liteLLM/LangChain which might do async.
        # If we are in an async function, we should ideally run this in a thread executor.
        
        result = await asyncio.to_thread(crew.kickoff, inputs=inputs)
        
        logger.info(f"✓ Crew execution completed successfully")
        logger.info(f"Result: {str(result)[:500]}...")  # Log first 500 chars
        
        if version_logger:
            version_logger.info("="*80)
            version_logger.info("🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO")
            version_logger.info("="*80)
            result_preview = str(result)[:500]
            version_logger.info(f"📤 RESULTADO FINAL: {result_preview}")
            if len(str(result)) > 500:
                version_logger.info(f"... (truncado, {len(str(result))} caracteres no total)")
            version_logger.info("="*80)
        
        # Determine agent name based on process type and result
        if crew_config.get('process') == 'hierarchical':
            agent_name = "Gerente da Equipe"
        else:
             # Last agent name logic
            if crew_kwargs['agents']:
                agent_name = crew_kwargs['agents'][-1].role
            else:
                agent_name = "Crew Agent"
        
        # Return dict with response and agent name
        return {"response": str(result), "agent_name": agent_name}

    except ImportError as e:
        error_msg = f"Error: crewai package not found. {str(e)}"
        logger.error(error_msg)
        return {"response": error_msg, "agent_name": "System"}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Exception during crew execution: {str(e)}")
        logger.error(f"Traceback:\n{error_trace}")
        return {"response": f"Execution Error: {str(e)}", "agent_name": "System"}
