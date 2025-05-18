"""
Mobile API for Tascade AI.

This module provides a RESTful API for mobile applications to interact with
Tascade AI's time tracking system.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import uuid

from ..core.task_timetracking import TaskTimeTrackingSystem
from ..core.timetracking.models import (
    TimeEntry, TimeEstimate, TimeEntryStatus, TimeEntryType, TimeEstimateType
)


class MobileTimeTrackingAPI:
    """Mobile API for time tracking functionality."""
    
    def __init__(self, 
                 time_tracking: TaskTimeTrackingSystem = None,
                 host: str = '0.0.0.0',
                 port: int = 5000,
                 debug: bool = False,
                 secret_key: str = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the mobile API.
        
        Args:
            time_tracking: Time tracking system instance
            host: Host to bind the server to
            port: Port to bind the server to
            debug: Whether to run in debug mode
            secret_key: Secret key for JWT authentication
            logger: Optional logger
        """
        self.time_tracking = time_tracking or TaskTimeTrackingSystem()
        self.host = host
        self.port = port
        self.debug = debug
        self.secret_key = secret_key or str(uuid.uuid4())
        self.logger = logger or logging.getLogger("tascade.mobile.api")
        
        # Initialize Flask app
        self.app = Flask("TascadeMobileAPI")
        self.app.config['SECRET_KEY'] = self.secret_key
        CORS(self.app)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register API routes."""
        # Authentication
        self.app.route('/api/auth/login', methods=['POST'])(self.login)
        
        # Time entries
        self.app.route('/api/time/entries', methods=['GET'])(self.get_time_entries)
        self.app.route('/api/time/entries', methods=['POST'])(self.create_time_entry)
        self.app.route('/api/time/entries/<entry_id>', methods=['GET'])(self.get_time_entry)
        self.app.route('/api/time/entries/<entry_id>', methods=['PUT'])(self.update_time_entry)
        self.app.route('/api/time/entries/<entry_id>', methods=['DELETE'])(self.delete_time_entry)
        
        # Work sessions
        self.app.route('/api/time/sessions', methods=['GET'])(self.get_sessions)
        self.app.route('/api/time/sessions/start', methods=['POST'])(self.start_session)
        self.app.route('/api/time/sessions/<session_id>/pause', methods=['POST'])(self.pause_session)
        self.app.route('/api/time/sessions/<session_id>/resume', methods=['POST'])(self.resume_session)
        self.app.route('/api/time/sessions/<session_id>/stop', methods=['POST'])(self.stop_session)
        self.app.route('/api/time/sessions/status', methods=['GET'])(self.get_session_status)
        
        # Time estimates
        self.app.route('/api/time/estimates', methods=['GET'])(self.get_estimates)
        self.app.route('/api/time/estimates', methods=['POST'])(self.create_estimate)
        self.app.route('/api/time/estimates/<estimate_id>', methods=['GET'])(self.get_estimate)
        self.app.route('/api/time/estimates/<estimate_id>', methods=['PUT'])(self.update_estimate)
        
        # Productivity
        self.app.route('/api/time/productivity', methods=['GET'])(self.get_productivity)
        
        # Reports
        self.app.route('/api/time/reports/<report_type>', methods=['GET'])(self.generate_report)
        
        # Sync
        self.app.route('/api/sync/upload', methods=['POST'])(self.sync_upload)
        self.app.route('/api/sync/download', methods=['GET'])(self.sync_download)
    
    def run(self) -> None:
        """Run the API server."""
        self.app.run(host=self.host, port=self.port, debug=self.debug)
    
    def _auth_required(self, f):
        """Decorator for routes that require authentication."""
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            
            if not token:
                return jsonify({'error': 'Authentication token is missing'}), 401
            
            try:
                # Remove 'Bearer ' prefix if present
                if token.startswith('Bearer '):
                    token = token[7:]
                
                # Verify token
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                request.user_id = payload.get('user_id')
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Authentication token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid authentication token'}), 401
            
            return f(*args, **kwargs)
        
        # Preserve the original function's name and docstring
        decorated.__name__ = f.__name__
        decorated.__doc__ = f.__doc__
        
        return decorated
    
    # Authentication routes
    
    def login(self):
        """Login endpoint."""
        data = request.get_json()
        
        # In a real implementation, this would validate credentials
        # For now, we'll just generate a token with the provided user_id
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Generate token
        token = jwt.encode(
            {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(days=30)
            },
            self.secret_key,
            algorithm='HS256'
        )
        
        return jsonify({
            'token': token,
            'user_id': user_id
        })
    
    # Time entry routes
    
    @_auth_required
    def get_time_entries(self):
        """Get time entries."""
        # Parse query parameters
        filters = {}
        
        if request.args.get('task_id'):
            filters['task_id'] = request.args.get('task_id')
        
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id')
        else:
            # Default to the authenticated user
            filters['user_id'] = request.user_id
        
        if request.args.get('from_date'):
            try:
                filters['from_date'] = datetime.fromisoformat(request.args.get('from_date'))
            except ValueError:
                return jsonify({'error': 'Invalid from_date format'}), 400
        
        if request.args.get('to_date'):
            try:
                filters['to_date'] = datetime.fromisoformat(request.args.get('to_date'))
            except ValueError:
                return jsonify({'error': 'Invalid to_date format'}), 400
        
        if request.args.get('tags'):
            filters['tags'] = request.args.get('tags').split(',')
        
        # Get entries
        try:
            entries = self.time_tracking.get_time_entries(filters)
            
            # Convert to JSON-serializable format
            result = [entry.to_dict() for entry in entries]
            
            return jsonify(result)
        except Exception as e:
            self.logger.error(f"Error getting time entries: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def create_time_entry(self):
        """Create a time entry."""
        data = request.get_json()
        
        # Set user_id from authenticated user if not provided
        if 'user_id' not in data:
            data['user_id'] = request.user_id
        
        # Parse dates
        if 'start_time' in data and isinstance(data['start_time'], str):
            try:
                data['start_time'] = datetime.fromisoformat(data['start_time'])
            except ValueError:
                return jsonify({'error': 'Invalid start_time format'}), 400
        
        if 'end_time' in data and isinstance(data['end_time'], str):
            try:
                data['end_time'] = datetime.fromisoformat(data['end_time'])
            except ValueError:
                return jsonify({'error': 'Invalid end_time format'}), 400
        
        # Create entry
        try:
            result = self.time_tracking.create_time_entry(**data)
            
            if not result.get('success'):
                return jsonify({'error': result.get('error')}), 400
            
            return jsonify(result), 201
        except Exception as e:
            self.logger.error(f"Error creating time entry: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def get_time_entry(self, entry_id):
        """Get a time entry by ID."""
        try:
            entry = self.time_tracking.entry_manager.get_entry(entry_id)
            
            if not entry:
                return jsonify({'error': 'Time entry not found'}), 404
            
            # Check if user has access to this entry
            if entry.user_id and entry.user_id != request.user_id:
                return jsonify({'error': 'Access denied'}), 403
            
            return jsonify(entry.to_dict())
        except Exception as e:
            self.logger.error(f"Error getting time entry: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def update_time_entry(self, entry_id):
        """Update a time entry."""
        data = request.get_json()
        
        # Get existing entry
        try:
            entry = self.time_tracking.entry_manager.get_entry(entry_id)
            
            if not entry:
                return jsonify({'error': 'Time entry not found'}), 404
            
            # Check if user has access to this entry
            if entry.user_id and entry.user_id != request.user_id:
                return jsonify({'error': 'Access denied'}), 403
            
            # Parse dates
            if 'start_time' in data and isinstance(data['start_time'], str):
                try:
                    data['start_time'] = datetime.fromisoformat(data['start_time'])
                except ValueError:
                    return jsonify({'error': 'Invalid start_time format'}), 400
            
            if 'end_time' in data and isinstance(data['end_time'], str):
                try:
                    data['end_time'] = datetime.fromisoformat(data['end_time'])
                except ValueError:
                    return jsonify({'error': 'Invalid end_time format'}), 400
            
            # Update entry
            success = self.time_tracking.entry_manager.update_entry(entry_id, **data)
            
            if not success:
                return jsonify({'error': 'Failed to update time entry'}), 400
            
            # Get updated entry
            updated_entry = self.time_tracking.entry_manager.get_entry(entry_id)
            
            return jsonify(updated_entry.to_dict())
        except Exception as e:
            self.logger.error(f"Error updating time entry: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def delete_time_entry(self, entry_id):
        """Delete a time entry."""
        try:
            entry = self.time_tracking.entry_manager.get_entry(entry_id)
            
            if not entry:
                return jsonify({'error': 'Time entry not found'}), 404
            
            # Check if user has access to this entry
            if entry.user_id and entry.user_id != request.user_id:
                return jsonify({'error': 'Access denied'}), 403
            
            # Delete entry
            success = self.time_tracking.entry_manager.delete_entry(entry_id)
            
            if not success:
                return jsonify({'error': 'Failed to delete time entry'}), 400
            
            return jsonify({'success': True})
        except Exception as e:
            self.logger.error(f"Error deleting time entry: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Work session routes
    
    @_auth_required
    def get_sessions(self):
        """Get active work sessions."""
        try:
            # Get user_id from query or authenticated user
            user_id = request.args.get('user_id') or request.user_id
            
            # Get active sessions
            sessions = self.time_tracking.get_active_sessions(user_id=user_id)
            
            return jsonify(sessions)
        except Exception as e:
            self.logger.error(f"Error getting sessions: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def start_session(self):
        """Start a new work session."""
        data = request.get_json()
        
        # Set user_id from authenticated user if not provided
        if 'user_id' not in data:
            data['user_id'] = request.user_id
        
        try:
            session_id = self.time_tracking.start_tracking(**data)
            
            if not session_id:
                return jsonify({'error': 'Failed to start session'}), 400
            
            # Get session data
            session_data = self.time_tracking.get_session(session_id)
            
            return jsonify({
                'session_id': session_id,
                'session': session_data
            }), 201
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def pause_session(self, session_id):
        """Pause a work session."""
        try:
            result = self.time_tracking.pause_tracking(session_id=session_id)
            
            if not result:
                return jsonify({'error': 'Failed to pause session'}), 400
            
            return jsonify(result)
        except Exception as e:
            self.logger.error(f"Error pausing session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def resume_session(self, session_id):
        """Resume a work session."""
        try:
            result = self.time_tracking.resume_tracking(session_id=session_id)
            
            if not result:
                return jsonify({'error': 'Failed to resume session'}), 400
            
            return jsonify(result)
        except Exception as e:
            self.logger.error(f"Error resuming session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def stop_session(self, session_id):
        """Stop a work session."""
        try:
            result = self.time_tracking.stop_tracking(session_id=session_id)
            
            if not result:
                return jsonify({'error': 'Failed to stop session'}), 400
            
            return jsonify(result)
        except Exception as e:
            self.logger.error(f"Error stopping session: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def get_session_status(self):
        """Get current tracking status."""
        try:
            # Get user_id from query or authenticated user
            user_id = request.args.get('user_id') or request.user_id
            
            status = self.time_tracking.get_tracking_status(user_id=user_id)
            
            return jsonify(status)
        except Exception as e:
            self.logger.error(f"Error getting tracking status: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Time estimate routes
    
    @_auth_required
    def get_estimates(self):
        """Get time estimates."""
        # Parse query parameters
        filters = {}
        
        if request.args.get('task_id'):
            filters['task_id'] = request.args.get('task_id')
        
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id')
        
        try:
            estimates = self.time_tracking.get_estimates(filters)
            
            # Convert to JSON-serializable format
            result = [estimate.to_dict() for estimate in estimates]
            
            return jsonify(result)
        except Exception as e:
            self.logger.error(f"Error getting time estimates: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def create_estimate(self):
        """Create a time estimate."""
        data = request.get_json()
        
        # Set created_by from authenticated user if not provided
        if 'created_by' not in data:
            data['created_by'] = request.user_id
        
        try:
            result = self.time_tracking.create_time_estimate(**data)
            
            if not result.get('success'):
                return jsonify({'error': result.get('error')}), 400
            
            return jsonify(result), 201
        except Exception as e:
            self.logger.error(f"Error creating time estimate: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def get_estimate(self, estimate_id):
        """Get a time estimate by ID."""
        try:
            estimate = self.time_tracking.estimate_manager.get_estimate(estimate_id)
            
            if not estimate:
                return jsonify({'error': 'Time estimate not found'}), 404
            
            return jsonify(estimate.to_dict())
        except Exception as e:
            self.logger.error(f"Error getting time estimate: {e}")
            return jsonify({'error': str(e)}), 500
    
    @_auth_required
    def update_estimate(self, estimate_id):
        """Update a time estimate."""
        data = request.get_json()
        
        try:
            estimate = self.time_tracking.estimate_manager.get_estimate(estimate_id)
            
            if not estimate:
                return jsonify({'error': 'Time estimate not found'}), 404
            
            # Update estimate
            success = self.time_tracking.estimate_manager.update_estimate(estimate_id, **data)
            
            if not success:
                return jsonify({'error': 'Failed to update time estimate'}), 400
            
            # Get updated estimate
            updated_estimate = self.time_tracking.estimate_manager.get_estimate(estimate_id)
            
            return jsonify(updated_estimate.to_dict())
        except Exception as e:
            self.logger.error(f"Error updating time estimate: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Productivity routes
    
    @_auth_required
    def get_productivity(self):
        """Get productivity metrics and insights."""
        # Parse query parameters
        user_id = request.args.get('user_id') or request.user_id
        
        start_date = None
        if request.args.get('start_date'):
            try:
                start_date = datetime.fromisoformat(request.args.get('start_date')).date()
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        end_date = None
        if request.args.get('end_date'):
            try:
                end_date = datetime.fromisoformat(request.args.get('end_date')).date()
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        task_ids = None
        if request.args.get('task_ids'):
            task_ids = request.args.get('task_ids').split(',')
        
        try:
            metrics, insights = self.time_tracking.analyze_productivity(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                task_ids=task_ids
            )
            
            result = {
                'metrics': metrics.to_dict(),
                'insights': [insight.to_dict() for insight in insights]
            }
            
            return jsonify(result)
        except Exception as e:
            self.logger.error(f"Error analyzing productivity: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Report routes
    
    @_auth_required
    def generate_report(self, report_type):
        """Generate a time tracking report."""
        # Parse query parameters
        filters = {}
        
        if request.args.get('task_id'):
            filters['task_id'] = request.args.get('task_id')
        
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id')
        else:
            # Default to the authenticated user
            filters['user_id'] = request.user_id
        
        if request.args.get('from_date'):
            try:
                filters['from_date'] = datetime.fromisoformat(request.args.get('from_date'))
            except ValueError:
                return jsonify({'error': 'Invalid from_date format'}), 400
        
        if request.args.get('to_date'):
            try:
                filters['to_date'] = datetime.fromisoformat(request.args.get('to_date'))
            except ValueError:
                return jsonify({'error': 'Invalid to_date format'}), 400
        
        output_format = request.args.get('format', 'json')
        
        try:
            report = self.time_tracking.generate_report(
                report_type=report_type,
                filters=filters,
                output_format=output_format
            )
            
            if not report:
                return jsonify({'error': 'Failed to generate report'}), 400
            
            if output_format == 'json':
                return jsonify(report)
            else:
                return report, 200, {'Content-Type': 'text/plain'}
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Sync routes
    
    @_auth_required
    def sync_upload(self):
        """Upload offline time entries for synchronization."""
        data = request.get_json()
        
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid data format'}), 400
        
        # Process time entries
        entries = data.get('time_entries', [])
        processed_entries = []
        
        for entry_data in entries:
            # Set user_id from authenticated user if not provided
            if 'user_id' not in entry_data:
                entry_data['user_id'] = request.user_id
            
            # Parse dates
            if 'start_time' in entry_data and isinstance(entry_data['start_time'], str):
                try:
                    entry_data['start_time'] = datetime.fromisoformat(entry_data['start_time'])
                except ValueError:
                    return jsonify({'error': f'Invalid start_time format in entry: {entry_data}'}), 400
            
            if 'end_time' in entry_data and isinstance(entry_data['end_time'], str):
                try:
                    entry_data['end_time'] = datetime.fromisoformat(entry_data['end_time'])
                except ValueError:
                    return jsonify({'error': f'Invalid end_time format in entry: {entry_data}'}), 400
            
            # Create entry
            try:
                result = self.time_tracking.create_time_entry(**entry_data)
                processed_entries.append({
                    'client_id': entry_data.get('client_id'),
                    'server_id': result.get('entry_id'),
                    'success': result.get('success', False),
                    'error': result.get('error')
                })
            except Exception as e:
                processed_entries.append({
                    'client_id': entry_data.get('client_id'),
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'time_entries': processed_entries
        })
    
    @_auth_required
    def sync_download(self):
        """Download time entries for offline use."""
        # Parse query parameters
        since = None
        if request.args.get('since'):
            try:
                since = datetime.fromisoformat(request.args.get('since'))
            except ValueError:
                return jsonify({'error': 'Invalid since format'}), 400
        
        # Get user_id from query or authenticated user
        user_id = request.args.get('user_id') or request.user_id
        
        try:
            # Get time entries
            filters = {'user_id': user_id}
            if since:
                filters['updated_since'] = since
            
            entries = self.time_tracking.get_time_entries(filters)
            
            # Get estimates
            estimates = self.time_tracking.get_estimates({'user_id': user_id})
            
            # Convert to JSON-serializable format
            result = {
                'time_entries': [entry.to_dict() for entry in entries],
                'time_estimates': [estimate.to_dict() for estimate in estimates],
                'sync_time': datetime.utcnow().isoformat()
            }
            
            return jsonify(result)
        except Exception as e:
            self.logger.error(f"Error syncing data: {e}")
            return jsonify({'error': str(e)}), 500
