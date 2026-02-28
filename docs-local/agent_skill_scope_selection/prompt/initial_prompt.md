
When using the CLI to configure agents and skills via the 'claude-mpm configure' command we are able to deploy and undeploy agents and skills.
This happens using the user or project scope, with the project scope being active by default. 
user scope allows modification of deployed agents and skills in the ~/.claude/agents and ~/.claude/skills directory. 
project scope allows modification of deployed agents and skills in the .claude/agents and .claude/skills directories within the project directory. 

Currently, we have two different code paths which allow configuration of agents and skills:
 1) CLI path - using the 'claude-mpm configure' command to deploy and undeploy agents and skills in either user or project scope. 
 2) API path - using the /config endpoints in the API, which require the project scope.

We need an abstraction which will allow us to unify these two code paths and provide a reusable code path for configuration of agents and skills, using specified scope.

Goals:
  - CLI path functionality must remain unaffected. Any changes should not break the existing CLI configuration process.
  - API path functionality must be able to select and utilize the project scope for configuration of agents and skills. The current API path implementation assumes operation using project scope only.
  - Test case coverage for both CLI and API paths should be maintained or improved to ensure reliability of the configuration process across both CLI and API paths.

Create an agent team to explore this from different angles: teammates to research specific angles (e.g. one to research cli path, one to research api path, one to research abstraction aspects, one on test relevance, one on implementation strategies, one to understand how the dashboard config process interacts with the backend). one teammate to play devil's advocate.
Write findings to docs-local/agent_skill_scope_selection/research/ for my review. 



