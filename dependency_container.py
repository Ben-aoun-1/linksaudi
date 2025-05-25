#!/usr/bin/env python3
# dependency_container.py - Simple dependency injection container

import logging
from typing import Dict, Any, Optional, Callable, Type

logger = logging.getLogger("market_intelligence")

class DependencyContainer:
    """Simple dependency injection container to manage system components"""
    
    def __init__(self):
        self._services = {}
        self._factories = {}
        self._singletons = {}
        self._initialized = False
    
    def register(self, name: str, implementation: Any) -> None:
        """Register a service implementation directly"""
        logger.debug(f"Registering service: {name}")
        self._services[name] = implementation
    
    def register_factory(self, name: str, factory: Callable[['DependencyContainer'], Any]) -> None:
        """Register a factory function that will create the service when needed"""
        logger.debug(f"Registering factory: {name}")
        self._factories[name] = factory
    
    def register_singleton_factory(self, name: str, factory: Callable[['DependencyContainer'], Any]) -> None:
        """Register a factory that will be called once to create a singleton instance"""
        logger.debug(f"Registering singleton factory: {name}")
        self._factories[name] = factory
        # Mark this as a singleton service
        self._singletons[name] = None
    
    def get(self, name: str) -> Any:
        """Get a service by name, creating it if needed via factory"""
        # If it's a singleton and we already created it, return the instance
        if name in self._singletons and self._singletons[name] is not None:
            return self._singletons[name]
        
        # If it's directly registered, return it
        if name in self._services:
            return self._services[name]
        
        # If it has a factory, create it
        if name in self._factories:
            logger.debug(f"Creating service via factory: {name}")
            service = self._factories[name](self)
            
            # If it's a singleton, store the instance
            if name in self._singletons:
                self._singletons[name] = service
            
            return service
        
        # Service not found
        logger.warning(f"Service not found: {name}")
        return None
    
    def has(self, name: str) -> bool:
        """Check if a service is registered"""
        return name in self._services or name in self._factories
    
    def initialize_container(self) -> None:
        """Initialize the container and any eager services"""
        if self._initialized:
            return
            
        logger.info("Initializing dependency container")
        self._initialized = True
    
    def has_legal_components(self) -> bool:
        """Check if legal compliance components are available"""
        legal_components = ['legal_rag_engine', 'legal_search_engine', 'legal_chatbot']
        return all(self.has(comp) for comp in legal_components)
    
    def get_legal_system_status(self) -> Dict[str, Any]:
        """Get the status of legal compliance system"""
        legal_components = ['legal_rag_engine', 'legal_search_engine', 'legal_chatbot']
        status = {
            'available': True,
            'components': {},
            'missing_components': []
        }
        
        for component in legal_components:
            if self.has(component):
                service = self.get(component)
                # Check if it's a mock service
                is_mock = 'Mock' in service.__class__.__name__ if service else True
                status['components'][component] = {
                    'available': not is_mock,
                    'type': 'mock' if is_mock else 'real'
                }
                if is_mock:
                    status['available'] = False
            else:
                status['components'][component] = {'available': False, 'type': 'missing'}
                status['missing_components'].append(component)
                status['available'] = False
        
        return status
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get an overview of all registered services"""
        overview = {
            'total_services': len(self._services),
            'total_factories': len(self._factories),
            'total_singletons': len(self._singletons),
            'services': list(self._services.keys()),
            'factories': list(self._factories.keys()),
            'singletons': list(self._singletons.keys()),
            'initialized': self._initialized
        }
        
        # Add legal system status
        overview['legal_system'] = self.get_legal_system_status()
        
        return overview
    
    def clear_cache(self) -> None:
        """Clear all cached singleton instances"""
        logger.info("Clearing dependency container cache")
        for name in self._singletons:
            self._singletons[name] = None
    
    def remove_service(self, name: str) -> bool:
        """Remove a service from the container"""
        removed = False
        
        if name in self._services:
            del self._services[name]
            removed = True
            
        if name in self._factories:
            del self._factories[name]
            removed = True
            
        if name in self._singletons:
            del self._singletons[name]
            removed = True
        
        if removed:
            logger.debug(f"Removed service: {name}")
        
        return removed
    
    def restart_legal_system(self) -> bool:
        """Restart the legal compliance system components"""
        try:
            legal_components = ['legal_rag_engine', 'legal_search_engine', 'legal_chatbot']
            
            # Clear existing legal components
            for component in legal_components:
                if component in self._singletons:
                    self._singletons[component] = None
            
            # Try to recreate legal components
            for component in legal_components:
                if self.has(component):
                    service = self.get(component)
                    if service:
                        logger.info(f"Restarted legal component: {component}")
                    else:
                        logger.warning(f"Failed to restart legal component: {component}")
                        return False
            
            logger.info("Legal compliance system restarted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error restarting legal system: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on all services"""
        health_status = {
            'overall_status': 'healthy',
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'services': {},
            'issues': []
        }
        
        # Check all registered services
        all_service_names = set(self._services.keys()) | set(self._factories.keys())
        
        for service_name in all_service_names:
            try:
                service = self.get(service_name)
                if service is None:
                    health_status['services'][service_name] = {
                        'status': 'failed',
                        'error': 'Service returned None'
                    }
                    health_status['issues'].append(f"{service_name}: Service returned None")
                elif 'Mock' in service.__class__.__name__:
                    health_status['services'][service_name] = {
                        'status': 'degraded',
                        'type': 'mock_service'
                    }
                    health_status['issues'].append(f"{service_name}: Using mock implementation")
                else:
                    health_status['services'][service_name] = {
                        'status': 'healthy',
                        'type': service.__class__.__name__
                    }
            except Exception as e:
                health_status['services'][service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_status['issues'].append(f"{service_name}: {str(e)}")
        
        # Determine overall status
        if any(s['status'] == 'error' for s in health_status['services'].values()):
            health_status['overall_status'] = 'critical'
        elif any(s['status'] == 'failed' for s in health_status['services'].values()):
            health_status['overall_status'] = 'degraded'
        elif any(s['status'] == 'degraded' for s in health_status['services'].values()):
            health_status['overall_status'] = 'degraded'
        
        return health_status
    
    def list_all_services(self) -> Dict[str, str]:
        """List all services with their types"""
        services_list = {}
        
        # Direct services
        for name in self._services:
            service = self._services[name]
            services_list[name] = f"Direct: {service.__class__.__name__}"
        
        # Factory services
        for name in self._factories:
            if name in self._singletons:
                if self._singletons[name] is not None:
                    services_list[name] = f"Singleton: {self._singletons[name].__class__.__name__}"
                else:
                    services_list[name] = "Singleton: Not yet created"
            else:
                services_list[name] = "Factory: Creates new instance each time"
        
        return services_list
    
    def get_service_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific service"""
        if not self.has(name):
            return {'error': f'Service {name} not found'}
        
        info = {
            'name': name,
            'exists': True,
            'type': None,
            'class_name': None,
            'is_singleton': name in self._singletons,
            'is_instantiated': False,
            'factory_available': name in self._factories,
            'direct_service': name in self._services
        }
        
        try:
            service = self.get(name)
            if service is not None:
                info['is_instantiated'] = True
                info['class_name'] = service.__class__.__name__
                info['type'] = 'mock' if 'Mock' in service.__class__.__name__ else 'real'
            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """Validate that all required dependencies are available"""
        validation_results = {
            'valid': True,
            'missing_dependencies': [],
            'mock_services': [],
            'failed_services': [],
            'recommendations': []
        }
        
        # Define critical dependencies
        critical_services = [
            'rag_engine', 'web_search', 'report_generator', 
            'market_report_system', 'pdf_exporter'
        ]
        
        optional_services = [
            'legal_rag_engine', 'legal_search_engine', 'legal_chatbot'
        ]
        
        # Check critical services
        for service_name in critical_services:
            if not self.has(service_name):
                validation_results['missing_dependencies'].append(service_name)
                validation_results['valid'] = False
            else:
                try:
                    service = self.get(service_name)
                    if service is None:
                        validation_results['failed_services'].append(service_name)
                        validation_results['valid'] = False
                    elif 'Mock' in service.__class__.__name__:
                        validation_results['mock_services'].append(service_name)
                except Exception as e:
                    validation_results['failed_services'].append(f"{service_name}: {str(e)}")
                    validation_results['valid'] = False
        
        # Check optional services (legal compliance)
        legal_available = 0
        for service_name in optional_services:
            if self.has(service_name):
                try:
                    service = self.get(service_name)
                    if service is not None and 'Mock' not in service.__class__.__name__:
                        legal_available += 1
                except Exception:
                    pass
        
        # Generate recommendations
        if validation_results['missing_dependencies']:
            validation_results['recommendations'].append(
                f"Install missing dependencies: {', '.join(validation_results['missing_dependencies'])}"
            )
        
        if validation_results['mock_services']:
            validation_results['recommendations'].append(
                f"Replace mock services with real implementations: {', '.join(validation_results['mock_services'])}"
            )
        
        if legal_available == 0:
            validation_results['recommendations'].append(
                "Legal compliance system is not available. Install legal compliance dependencies if needed."
            )
        elif legal_available < len(optional_services):
            validation_results['recommendations'].append(
                f"Legal compliance system is partially available ({legal_available}/{len(optional_services)} components)"
            )
        
        return validation_results

# Create a singleton container instance
container = DependencyContainer()

def get_container() -> DependencyContainer:
    """Get the singleton container instance"""
    return container