"""
Project Manager for XRD Analysis

Manages project folders and saves all analysis data, images, and metadata
for each XRD file analysis session.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import numpy as np


class ProjectManager:
    """Manages XRD analysis projects"""
    
    def __init__(self, projects_root: Optional[str] = None):
        if projects_root is None:
            # Default to projects folder in workspace
            projects_root = Path(__file__).parent.parent.parent / "projects"
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(exist_ok=True)
        
        self.current_project: Optional[Path] = None
        self.current_project_info: Dict[str, Any] = {}
    
    def create_project(self, file_name: str, file_path: str) -> Path:
        """
        Create a new project folder for an analysis
        
        Args:
            file_name: Name of the XRD file
            file_path: Full path to the XRD file
            
        Returns:
            Path to the project folder
        """
        # Create project name: filename_timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(file_name).stem.replace(" ", "_").replace(".", "_")
        project_name = f"{safe_name}_{timestamp}"
        
        project_path = self.projects_root / project_name
        project_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (project_path / "original_data").mkdir(exist_ok=True)
        (project_path / "processed_data").mkdir(exist_ok=True)
        (project_path / "analysis").mkdir(exist_ok=True)
        (project_path / "visualizations").mkdir(exist_ok=True)
        (project_path / "reference_patterns").mkdir(exist_ok=True)
        
        # Initialize project info
        self.current_project = project_path
        self.current_project_info = {
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "source_file": file_name,
            "source_file_path": str(file_path),
            "analysis_steps": [],
            "reference_patterns_used": [],
            "peak_detection": {},
            "match_results": {}
        }
        
        # Save initial project info
        self.save_project_info()
        
        return project_path
    
    def save_original_data(self, two_theta: np.ndarray, intensity: np.ndarray,
                          wavelength: Optional[float] = None,
                          metadata: Optional[Dict] = None):
        """Save original XRD data"""
        if self.current_project is None:
            return
        
        data_path = self.current_project / "original_data" / "raw_data.json"
        
        data = {
            "two_theta": two_theta.tolist(),
            "intensity": intensity.tolist(),
            "wavelength": wavelength,
            "metadata": metadata or {},
            "saved_at": datetime.now().isoformat()
        }
        
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save metadata separately
        if metadata:
            meta_path = self.current_project / "original_data" / "metadata.json"
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        self.current_project_info["original_data_points"] = len(two_theta)
        self.current_project_info["two_theta_range"] = [float(np.min(two_theta)), float(np.max(two_theta))]
        self.save_project_info()
    
    def save_processed_data(self, step_name: str, two_theta: np.ndarray,
                           intensity: np.ndarray, parameters: Optional[Dict] = None):
        """Save processed data after each processing step"""
        if self.current_project is None:
            return
        
        data_path = self.current_project / "processed_data" / f"{step_name}.json"
        
        data = {
            "step": step_name,
            "two_theta": two_theta.tolist(),
            "intensity": intensity.tolist(),
            "parameters": parameters or {},
            "saved_at": datetime.now().isoformat()
        }
        
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update project info
        if "analysis_steps" not in self.current_project_info:
            self.current_project_info["analysis_steps"] = []
        
        self.current_project_info["analysis_steps"].append({
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "parameters": parameters or {}
        })
        self.save_project_info()
    
    def save_visualization(self, image_name: str, figure):
        """Save visualization image"""
        if self.current_project is None:
            return
        
        image_path = self.current_project / "visualizations" / f"{image_name}.png"
        figure.savefig(image_path, dpi=150, bbox_inches='tight')
    
    def save_peak_detection(self, peaks: List, method: str, parameters: Dict):
        """Save peak detection results"""
        if self.current_project is None:
            return
        
        peaks_data = []
        for peak in peaks:
            peaks_data.append({
                "two_theta": float(peak.two_theta),
                "intensity": float(peak.intensity),
                "index": int(peak.index),
                "width": float(peak.width) if peak.width else None,
                "prominence": float(peak.prominence) if peak.prominence else None
            })
        
        data = {
            "method": method,
            "parameters": parameters,
            "peaks": peaks_data,
            "peak_count": len(peaks),
            "saved_at": datetime.now().isoformat()
        }
        
        analysis_path = self.current_project / "analysis" / "peaks_detected.json"
        with open(analysis_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.current_project_info["peak_detection"] = {
            "method": method,
            "parameters": parameters,
            "peak_count": len(peaks),
            "timestamp": datetime.now().isoformat()
        }
        self.save_project_info()
    
    def save_reference_match(self, reference_name: str, match_result: Dict,
                            reference_pattern_data: Optional[Dict] = None):
        """Save reference pattern matching results"""
        if self.current_project is None:
            return
        
        match_data = {
            "reference_name": reference_name,
            "match_score": float(match_result.get('match_score', 0)),
            "matched_peaks_count": len(match_result.get('matched_peaks', [])),
            "total_reference_peaks": len(match_result.get('unmatched_reference', [])) + len(match_result.get('matched_peaks', [])),
            "matched_peaks": [
                {
                    "detected_two_theta": float(mp[0].two_theta),
                    "detected_intensity": float(mp[0].intensity),
                    "reference_two_theta": float(mp[1][1]),
                    "reference_intensity": float(mp[1][2])
                }
                for mp in match_result.get('matched_peaks', [])
            ],
            "unmatched_detected": [
                {"two_theta": float(p.two_theta), "intensity": float(p.intensity)}
                for p in match_result.get('unmatched_detected', [])
            ],
            "unmatched_reference": [
                {"two_theta": float(p[0]), "intensity": float(p[1])}
                for p in match_result.get('unmatched_reference', [])
            ],
            "saved_at": datetime.now().isoformat()
        }
        
        # Save match result
        match_path = self.current_project / "analysis" / f"match_{reference_name.replace(' ', '_')}.json"
        with open(match_path, 'w') as f:
            json.dump(match_data, f, indent=2)
        
        # Save reference pattern data if provided
        if reference_pattern_data:
            ref_path = self.current_project / "reference_patterns" / f"{reference_name.replace(' ', '_')}.json"
            with open(ref_path, 'w') as f:
                json.dump(reference_pattern_data, f, indent=2)
        
        # Update project info
        if "reference_patterns_used" not in self.current_project_info:
            self.current_project_info["reference_patterns_used"] = []
        
        self.current_project_info["reference_patterns_used"].append({
            "name": reference_name,
            "match_score": float(match_result.get('match_score', 0)),
            "timestamp": datetime.now().isoformat()
        })
        
        self.current_project_info["match_results"][reference_name] = {
            "match_score": float(match_result.get('match_score', 0)),
            "matched_peaks": len(match_result.get('matched_peaks', []))
        }
        self.save_project_info()
    
    def save_project_info(self):
        """Save project information file"""
        if self.current_project is None:
            return
        
        info_path = self.current_project / "project_info.json"
        with open(info_path, 'w') as f:
            json.dump(self.current_project_info, f, indent=2)
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get summary of current project"""
        if self.current_project is None:
            return {}
        
        return {
            "project_path": str(self.current_project),
            "project_name": self.current_project_info.get("project_name"),
            "source_file": self.current_project_info.get("source_file"),
            "created_at": self.current_project_info.get("created_at"),
            "analysis_steps": len(self.current_project_info.get("analysis_steps", [])),
            "peaks_detected": self.current_project_info.get("peak_detection", {}).get("peak_count", 0),
            "reference_patterns_used": len(self.current_project_info.get("reference_patterns_used", []))
        }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        projects = []
        for project_dir in sorted(self.projects_root.iterdir(), reverse=True):
            if project_dir.is_dir():
                info_path = project_dir / "project_info.json"
                if info_path.exists():
                    try:
                        with open(info_path, 'r') as f:
                            info = json.load(f)
                            projects.append({
                                "name": project_dir.name,
                                "path": str(project_dir),
                                "created_at": info.get("created_at"),
                                "source_file": info.get("source_file"),
                                "analysis_steps": len(info.get("analysis_steps", []))
                            })
                    except:
                        pass
        return projects
    
    def load_project(self, project_path: str) -> Dict[str, Any]:
        """Load a project"""
        project_path = Path(project_path)
        info_path = project_path / "project_info.json"
        
        if not info_path.exists():
            raise FileNotFoundError(f"Project info not found: {info_path}")
        
        with open(info_path, 'r') as f:
            self.current_project_info = json.load(f)
        
        self.current_project = project_path
        return self.current_project_info

