#!/usr/bin/env python3
"""
Deploy EVE-NG Lab Configuration from VS Code
This script demonstrates how to deploy lab configurations from VS Code using the EVE-NG MCP Server
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eveng_mcp_server.client import EVENGClient
from eveng_mcp_server.exceptions import EVENGConnectionError, EVENGAuthenticationError


class LabDeployer:
    """Deploy EVE-NG lab configurations from VS Code"""
    
    def __init__(self):
        self.client = EVENGClient()
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to EVE-NG server using environment variables"""
        try:
            host = os.getenv('EVENG_HOST', 'eve.local')
            username = os.getenv('EVENG_USERNAME', 'admin')
            password = os.getenv('EVENG_PASSWORD', 'eve')
            port = int(os.getenv('EVENG_PORT', '80'))
            protocol = os.getenv('EVENG_PROTOCOL', 'http')
            
            print(f"üîå Connecting to EVE-NG server at {protocol}://{host}:{port}")
            
            success = await self.client.connect(
                host=host,
                username=username,
                password=password,
                port=port,
                protocol=protocol
            )
            
            if success:
                print("‚ú?Connected to EVE-NG server successfully")
                self.connected = True
                return True
            else:
                print("‚ù?Failed to connect to EVE-NG server")
                return False
                
        except EVENGAuthenticationError as e:
            print(f"‚ù?Authentication failed: {e}")
            return False
        except EVENGConnectionError as e:
            print(f"‚ù?Connection error: {e}")
            return False
        except Exception as e:
            print(f"‚ù?Unexpected error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from EVE-NG server"""
        if self.connected:
            await self.client.disconnect()
            self.connected = False
            print("üîå Disconnected from EVE-NG server")
    
    def load_lab_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """Load lab configuration from file"""
        try:
            config_file = Path(config_path)
            
            if not config_file.exists():
                print(f"‚ù?Configuration file not found: {config_path}")
                return None
            
            print(f"üìÑ Loading lab configuration from {config_path}")
            
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() == '.json':
                    config = json.load(f)
                elif config_file.suffix.lower() in ['.yaml', '.yml']:
                    import yaml
                    config = yaml.safe_load(f)
                else:
                    print(f"‚ù?Unsupported file format: {config_file.suffix}")
                    return None
            
            # Validate required fields
            required_fields = ['name', 'description']
            for field in required_fields:
                if field not in config:
                    print(f"‚ù?Missing required field: {field}")
                    return None
            
            print(f"‚ú?Loaded configuration for lab: {config['name']}")
            return config
            
        except json.JSONDecodeError as e:
            print(f"‚ù?Invalid JSON format: {e}")
            return None
        except Exception as e:
            print(f"‚ù?Error loading configuration: {e}")
            return None
    
    async def deploy_lab(self, config: Dict[str, Any]) -> bool:
        """Deploy lab configuration to EVE-NG"""
        try:
            lab_name = config['name']
            lab_path = f"/{lab_name}.unl"
            
            print(f"üöÄ Deploying lab: {lab_name}")
            
            # Check if lab already exists
            existing_labs = await self.client.list_labs()
            if lab_path in existing_labs:
                print(f"‚ö†Ô∏è  Lab {lab_name} already exists")
                response = input("Do you want to overwrite it? (y/N): ")
                if response.lower() != 'y':
                    print("‚ù?Deployment cancelled")
                    return False
                
                # Delete existing lab
                print(f"üóëÔ∏? Deleting existing lab: {lab_name}")
                await self.client.delete_lab(lab_path)
            
            # Create new lab
            print(f"üìù Creating lab: {lab_name}")
            result = await self.client.create_lab(
                name=lab_name,
                description=config.get('description', ''),
                author=config.get('author', 'VS Code Deployer'),
                version=config.get('version', '1.0'),
                path=config.get('path', '/')
            )
            
            if result.get('status') != 'success':
                print(f"‚ù?Failed to create lab: {result}")
                return False
            
            print(f"‚ú?Lab created successfully")
            
            # Deploy nodes
            if 'nodes' in config:
                await self.deploy_nodes(lab_path, config['nodes'])
            
            # Deploy networks
            if 'networks' in config:
                await self.deploy_networks(lab_path, config['networks'])
            
            # Deploy connections
            if 'connections' in config:
                await self.deploy_connections(lab_path, config['connections'])
            
            print(f"üéâ Lab {lab_name} deployed successfully!")
            return True
            
        except Exception as e:
            print(f"‚ù?Error deploying lab: {e}")
            return False
    
    async def deploy_nodes(self, lab_path: str, nodes: Dict[str, Any]):
        """Deploy nodes to the lab"""
        print(f"üñ•Ô∏? Deploying {len(nodes)} nodes...")
        
        for node_name, node_config in nodes.items():
            try:
                print(f"  üì¶ Adding node: {node_name}")
                
                result = await self.client.add_node(
                    lab_path=lab_path,
                    template=node_config.get('template', 'vios'),
                    name=node_name,
                    left=node_config.get('left', 25),
                    top=node_config.get('top', 25),
                    ram=node_config.get('ram', 512),
                    ethernet=node_config.get('ethernet', 4),
                    console=node_config.get('console', 'telnet'),
                    delay=node_config.get('delay', 0)
                )
                
                if result.get('status') == 'success':
                    print(f"    ‚ú?Node {node_name} added successfully")
                else:
                    print(f"    ‚ù?Failed to add node {node_name}: {result}")
                    
            except Exception as e:
                print(f"    ‚ù?Error adding node {node_name}: {e}")
    
    async def deploy_networks(self, lab_path: str, networks: Dict[str, Any]):
        """Deploy networks to the lab"""
        print(f"üåê Deploying {len(networks)} networks...")
        
        for network_name, network_config in networks.items():
            try:
                print(f"  üîó Adding network: {network_name}")
                
                result = await self.client.create_lab_network(
                    lab_path=lab_path,
                    network_type=network_config.get('type', 'bridge'),
                    name=network_name,
                    left=network_config.get('left', 50),
                    top=network_config.get('top', 100)
                )
                
                if result.get('status') == 'success':
                    print(f"    ‚ú?Network {network_name} added successfully")
                else:
                    print(f"    ‚ù?Failed to add network {network_name}: {result}")
                    
            except Exception as e:
                print(f"    ‚ù?Error adding network {network_name}: {e}")
    
    async def deploy_connections(self, lab_path: str, connections: list):
        """Deploy connections between nodes and networks"""
        print(f"üîå Deploying {len(connections)} connections...")
        
        for connection in connections:
            try:
                source = connection.get('source')
                target = connection.get('target')
                source_port = connection.get('source_port', 0)
                target_port = connection.get('target_port', 0)
                
                print(f"  üîó Connecting {source}:{source_port} to {target}:{target_port}")
                
                result = await self.client.connect_node_to_network(
                    lab_path=lab_path,
                    node_id=source,
                    network_id=target,
                    interface=source_port
                )
                
                if result.get('status') == 'success':
                    print(f"    ‚ú?Connection established successfully")
                else:
                    print(f"    ‚ù?Failed to establish connection: {result}")
                    
            except Exception as e:
                print(f"    ‚ù?Error establishing connection: {e}")
    
    async def validate_deployment(self, lab_path: str) -> bool:
        """Validate the deployed lab"""
        try:
            print(f"üîç Validating deployment...")
            
            # Get lab details
            lab_details = await self.client.get_lab_details(lab_path)
            
            if not lab_details:
                print("‚ù?Failed to get lab details")
                return False
            
            nodes = lab_details.get('nodes', {})
            networks = lab_details.get('networks', {})
            
            print(f"‚ú?Validation complete:")
            print(f"  üì¶ Nodes: {len(nodes)}")
            print(f"  üåê Networks: {len(networks)}")
            
            return True
            
        except Exception as e:
            print(f"‚ù?Validation error: {e}")
            return False


async def main():
    """Main deployment function"""
    if len(sys.argv) != 2:
        print("Usage: python deploy_lab.py <config_file>")
        print("Example: python deploy_lab.py labs/enterprise-network.json")
        sys.exit(1)
    
    config_file = sys.argv[1]
    deployer = LabDeployer()
    
    try:
        # Connect to EVE-NG
        if not await deployer.connect():
            sys.exit(1)
        
        # Load configuration
        config = deployer.load_lab_config(config_file)
        if not config:
            sys.exit(1)
        
        # Deploy lab
        if await deployer.deploy_lab(config):
            # Validate deployment
            lab_path = f"/{config['name']}.unl"
            await deployer.validate_deployment(lab_path)
            print(f"üéâ Deployment completed successfully!")
        else:
            print(f"‚ù?Deployment failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n‚ö†Ô∏è  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"‚ù?Unexpected error: {e}")
        sys.exit(1)
    finally:
        await deployer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
