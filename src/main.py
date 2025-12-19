"""Command line entrypoint for the ASTRO autonomous agent ecosystem."""

from __future__ import annotations

import argparse
import asyncio
import uuid
from typing import Any, Dict, List

from agents.base_agent import TaskResult
from agents.code_agent import CodeAgent
from agents.filesystem_agent import FileSystemAgent
from core.engine import AgentConfig, AgentEngine, Task, Workflow
from core.llm_factory import LLMFactory
from core.nl_interface import NaturalLanguageInterface
from core.task_queue import WorkflowPriority
from monitoring.monitoring_dashboard import MonitoringDashboard
from utils.config_loader import ConfigLoader
from utils.logger import configure_logging, get_logger


logger = get_logger("MainApplication")


class UnavailableAgent:
    """Stub agent used when an implementation is unavailable."""

    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.is_available = False

    async def execute_task(
        self, task: Dict[str, Any] | None = None, context: Any | None = None
    ) -> TaskResult:
        return TaskResult(
            success=False,
            error_message=f"Agent {self.agent_id} unavailable",
            result_data={"agent_id": self.agent_id, "available": False},
        )


class AutonomousAgentEcosystem:
    """Main application class orchestrating agents, workflows, and monitoring."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        runtime_config = config or {}

        self.engine = AgentEngine()
        self.dashboard = MonitoringDashboard()
        self.agents: Dict[str, Any] = {}
        self.workflows: Dict[str, Workflow] = {}

        self.config_loader = ConfigLoader()
        self.loaded_configs = self.config_loader.load_configs()
        self.config = runtime_config

        logger.info("Autonomous Agent Ecosystem initialized")

    async def initialize_agents(self) -> None:
        """Initialize and register all configured agents."""

        logger.info("Initializing agents...")

        agent_configs = self.loaded_configs.get("agents", {})
        llm_config = self.loaded_configs.get("llm", {})

        provider = self.config.get("llm_provider") or getattr(
            llm_config, "provider", "openai"
        )
        api_key = self.config.get("api_key") or getattr(llm_config, "api_key", None)
        base_url = self.config.get("api_base") or getattr(llm_config, "api_base", None)
        model_name = self.config.get("model_name") or getattr(
            llm_config, "model_name", "gpt-3.5-turbo"
        )

        llm_client = LLMFactory.create_client(
            provider=provider, api_key=api_key, base_url=base_url
        )

        code_config_dict = agent_configs.get("code_agent_001", {})
        code_config_dict.update(
            {
                "llm_provider": provider,
                "model_name": model_name,
                "api_key": api_key,
                "api_base": base_url,
            }
        )

        fs_config_dict = agent_configs.get("filesystem_agent_001", {})

        # TODO: research agent currently unavailable pending implementation
        research_agent = None

        code_agent = CodeAgent(
            agent_id="code_agent_001", config=code_config_dict, llm_client=llm_client
        )
        fs_agent = FileSystemAgent(
            agent_id="filesystem_agent_001", config=fs_config_dict
        )

        research_config = AgentConfig(
            agent_id="research_agent_001",
            capabilities=[
                "web_search",
                "content_extraction",
                "knowledge_synthesis",
                "data_processing",
            ],
            max_concurrent_tasks=2,
            reliability_score=0.92,
            cost_per_operation=1.5,
        )

        code_config = AgentConfig(
            agent_id="code_agent_001",
            capabilities=[
                "code_generation",
                "code_optimization",
                "debugging",
                "optimization",
            ],
            max_concurrent_tasks=code_config_dict.get("max_concurrent_tasks", 2),
            reliability_score=0.88,
            cost_per_operation=2.0,
        )

        filesystem_config = AgentConfig(
            agent_id="filesystem_agent_001",
            capabilities=["data_processing", "file_operations"],
            max_concurrent_tasks=fs_config_dict.get("max_concurrent_tasks", 5),
            reliability_score=0.99,
            cost_per_operation=0.5,
        )

        await self._safe_register_agent(research_config, research_agent)
        await self._safe_register_agent(code_config, code_agent)
        await self._safe_register_agent(filesystem_config, fs_agent)

        logger.info("Agents initialized and registered successfully")

    async def _safe_register_agent(
        self, config: AgentConfig, instance: Any | None
    ) -> None:
        """Register an agent or a stub implementation when unavailable."""

        agent_instance = instance
        if agent_instance is None:
            logger.warning(
                "Agent implementation unavailable; registering stub", extra={"agent_id": config.agent_id}
            )
            agent_instance = UnavailableAgent(config.agent_id, config.capabilities)

        await self.engine.register_agent(config, instance=agent_instance)
        self.agents[config.agent_id] = agent_instance

        self.dashboard.register_agent(
            config.agent_id, {"state": "active", "capabilities": config.capabilities}
        )

    async def create_sample_workflows(self) -> None:
        """Create sample workflows from YAML/JSON configuration files."""

        logger.info("Creating sample workflows from config...")

        workflow_path_override = self.config.get("sample_workflows")
        test_workflows = self.config_loader.load_workflows(
            workflow_path=workflow_path_override
        )

        if not test_workflows:
            logger.info("No sample workflows loaded; skipping submission.")
            return

        for wf_name, wf_config in test_workflows.items():
            if not isinstance(wf_config, dict):
                logger.warning("Skipping workflow '%s' because it is not a mapping", wf_name)
                continue

            try:
                workflow = Workflow(
                    workflow_id=f"wf_{wf_name}_{uuid.uuid4().hex[:8]}",
                    name=wf_config["description"],
                    tasks=[
                        Task(
                            task_id=f"{task['id']}_{uuid.uuid4().hex[:8]}",
                            description=task["instruction"],
                            required_capabilities=[task["capability"]],
                            payload=task.get("payload", {}),
                            priority=WorkflowPriority(wf_config["priority"]),
                        )
                        for task in wf_config["tasks"]
                    ],
                    priority=WorkflowPriority(wf_config["priority"]),
                    max_execution_time=wf_config.get("max_execution_time", 3600.0),
                    cost_budget=wf_config.get("budget", 100.0),
                )
            except KeyError as exc:
                logger.error("Workflow '%s' missing required field: %s. Skipping.", wf_name, exc)
                continue

            self.workflows[workflow.workflow_id] = workflow
            await self.engine.submit_workflow(workflow)
            logger.info(
                "Submitted test workflow: %s (%s)", wf_name, wf_config.get("description", "")
            )

    async def start_system(self) -> None:
        """Start the autonomous agent ecosystem and run for the configured duration."""

        logger.info("🚀 Starting Autonomous Agent Ecosystem (PRODUCTION MODE)")
        logger.info("=" * 60)

        try:
            await self.initialize_agents()
            await self.create_sample_workflows()

            engine_task = asyncio.create_task(self.engine.start_engine())
            monitoring_task = asyncio.create_task(self.dashboard.start_monitoring())

            duration = self.config.get("duration", 120)
            logger.info("System running for %s seconds... Press Ctrl+C to stop.", duration)
            logger.info("=" * 60)

            await asyncio.sleep(duration)

            engine_task.cancel()
            monitoring_task.cancel()

            try:
                await engine_task
                await monitoring_task
            except asyncio.CancelledError:
                pass

            logger.info("✅ System shutdown completed gracefully")

        except KeyboardInterrupt:
            logger.info("🛑 System interrupted by user")
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("❌ System error: %s", str(exc), exc_info=True)
        finally:
            await self.generate_final_report()

    async def generate_final_report(self) -> None:
        """Generate a final execution summary for monitoring."""

        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL SYSTEM REPORT")
        logger.info("=" * 60)

        system_health = self.dashboard.get_system_health()
        logger.info(
            "📈 System Health Score: %.2f (%s)",
            system_health["health_score"],
            system_health["status"],
        )
        logger.info("🤖 Active Agents: %s", system_health["active_agents_count"])

        logger.info("\n" + "-" * 40)
        logger.info("_WORKFLOW EXECUTION SUMMARY_")
        logger.info("-" * 40)

        for workflow in self.workflows.values():
            completed_tasks = sum(
                1 for task in workflow.tasks if task.task_id in self.engine.completed_tasks
            )
            total_tasks = len(workflow.tasks)
            status = (
                "✅ Completed"
                if completed_tasks == total_tasks
                else f"⚠️ {completed_tasks}/{total_tasks} Tasks"
            )
            logger.info("\n%s: %s", workflow.name, status)

        logger.info("\n" + "=" * 60)
        logger.info("✨ EXECUTION COMPLETE")
        logger.info("=" * 60)


def parse_arguments(args: List[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Autonomous Agent Ecosystem")
    parser.add_argument(
        "--duration",
        type=int,
        default=120,
        help="Duration to run the system in seconds (default: 120)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    parser.add_argument(
        "--llm-provider",
        type=str,
        dest="llm_provider",
        help="LLM provider to use (openai, openrouter, ollama)",
    )
    parser.add_argument("--model-name", type=str, help="Model name to use")
    parser.add_argument("--api-key", type=str, dest="api_key", help="API key for the LLM provider")
    parser.add_argument("--api-base", type=str, dest="api_base", help="Base URL for the LLM API")
    parser.add_argument(
        "--sample-workflows",
        type=str,
        dest="sample_workflows",
        help="Path to sample workflows YAML file (relative to config/ by default)",
    )

    return parser.parse_args(args)


async def run_main() -> None:
    """Main entry point for CLI execution."""

    args = parse_arguments()
    configure_logging(log_level="DEBUG" if args.debug else "INFO", log_to_file=True)

    config = {k: v for k, v in vars(args).items() if v is not None}
    ecosystem = AutonomousAgentEcosystem(config=config)

    if args.interactive:
        await interactive_mode(ecosystem, args)
    else:
        await ecosystem.start_system()


async def interactive_mode(
    ecosystem: AutonomousAgentEcosystem, args: argparse.Namespace
) -> None:
    """Run the interactive CLI loop."""

    await ecosystem.initialize_agents()

    engine_task = asyncio.create_task(ecosystem.engine.start_engine())
    monitor_task = asyncio.create_task(ecosystem.dashboard.start_monitoring())

    llm_config = ecosystem.loaded_configs.get("llm")
    llm_client = LLMFactory.create_client(
        provider=args.llm_provider or getattr(llm_config, "provider", "openai"),
        api_key=args.api_key or getattr(llm_config, "api_key", None),
        base_url=args.api_base or getattr(llm_config, "api_base", None),
    )

    nl_interface = NaturalLanguageInterface(
        engine=ecosystem.engine,
        llm_client=llm_client,
        model_name=args.model_name or getattr(llm_config, "model_name", "gpt-3.5-turbo"),
    )

    print("\n💬 Interactive Mode Enabled. Type your request (or 'exit'):")
    while True:
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, ">> ")
        if user_input.lower() in ["exit", "quit"]:
            break

        try:
            workflow_id = await nl_interface.process_request(user_input)
            if workflow_id:
                await ecosystem.engine.process_workflow(workflow_id)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to process request: %s", exc, exc_info=True)

    engine_task.cancel()
    monitor_task.cancel()

    try:
        await engine_task
        await monitor_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(run_main())
