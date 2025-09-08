"""
Data management and versioning for Browser.AI MLOps

This module provides data management capabilities including:
- Conversation history versioning
- DOM snapshot management  
- Training data collection and curation
- Data lineage tracking
- Data quality monitoring
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ConversationRecord(BaseModel):
	"""Record of a conversation between user and agent"""
	conversation_id: str
	session_id: str
	timestamp: datetime = Field(default_factory=datetime.now)
	
	# Conversation content
	messages: List[Dict[str, Any]] = Field(default_factory=list)
	task_description: str
	task_category: Optional[str] = None
	
	# Execution details
	success: Optional[bool] = None
	completion_time_seconds: Optional[float] = None
	steps_taken: int = 0
	errors_encountered: List[str] = Field(default_factory=list)
	
	# Model information
	model_id: Optional[str] = None
	model_version: Optional[str] = None
	
	# Data quality markers
	quality_score: Optional[float] = None
	reviewed: bool = False
	include_in_training: bool = True
	
	# Metadata
	tags: List[str] = Field(default_factory=list)
	annotations: Dict[str, Any] = Field(default_factory=dict)


class DOMSnapshot(BaseModel):
	"""DOM snapshot with metadata"""
	snapshot_id: str
	conversation_id: str
	timestamp: datetime = Field(default_factory=datetime.now)
	step_number: int
	
	# DOM content
	url: str
	title: str
	dom_hash: str
	dom_size_bytes: int
	element_count: int
	
	# Action context
	action_type: Optional[str] = None
	action_success: Optional[bool] = None
	screenshot_path: Optional[str] = None
	
	# Metadata
	tags: List[str] = Field(default_factory=list)


class DataVersion(BaseModel):
	"""Data version information"""
	version_id: str
	version_name: str
	created_at: datetime = Field(default_factory=datetime.now)
	created_by: str
	description: Optional[str] = None
	
	# Version statistics
	total_conversations: int = 0
	total_dom_snapshots: int = 0
	success_rate: Optional[float] = None
	avg_quality_score: Optional[float] = None
	
	# Data filters used
	date_range: Optional[Dict[str, str]] = None
	model_filters: List[str] = Field(default_factory=list)
	quality_threshold: Optional[float] = None
	
	# Parent version (for incremental versions)
	parent_version: Optional[str] = None


class DataManager:
	"""Main data management and versioning system"""
	
	def __init__(self, data_dir: Union[str, Path] = "mlops/data"):
		self.data_dir = Path(data_dir)
		self.data_dir.mkdir(parents=True, exist_ok=True)
		
		# Create subdirectories
		(self.data_dir / "conversations").mkdir(exist_ok=True)
		(self.data_dir / "dom_snapshots").mkdir(exist_ok=True)
		(self.data_dir / "versions").mkdir(exist_ok=True)
		(self.data_dir / "raw").mkdir(exist_ok=True)
		(self.data_dir / "processed").mkdir(exist_ok=True)
		
		self.logger = logging.getLogger(__name__)
		
	def store_conversation(self, conversation: ConversationRecord) -> str:
		"""Store a conversation record"""
		# Create hash-based filename for deduplication
		content_hash = hashlib.md5(
			json.dumps(conversation.messages, sort_keys=True).encode()
		).hexdigest()[:12]
		
		filename = f"{conversation.conversation_id}_{content_hash}.json"
		filepath = self.data_dir / "conversations" / filename
		
		# Save conversation
		with open(filepath, 'w') as f:
			json.dump(conversation.model_dump(), f, indent=2, default=str)
			
		self.logger.info(f"Stored conversation: {conversation.conversation_id}")
		return str(filepath)
		
	def store_dom_snapshot(
		self,
		conversation_id: str,
		step_number: int,
		url: str,
		title: str,
		dom_content: str,
		**metadata
	) -> str:
		"""Store a DOM snapshot"""
		
		# Calculate DOM hash and metrics
		dom_hash = hashlib.md5(dom_content.encode()).hexdigest()
		dom_size = len(dom_content.encode())
		element_count = dom_content.count('<')  # Rough estimate
		
		snapshot = DOMSnapshot(
			snapshot_id=f"{conversation_id}_{step_number}_{int(datetime.now().timestamp())}",
			conversation_id=conversation_id,
			step_number=step_number,
			url=url,
			title=title,
			dom_hash=dom_hash,
			dom_size_bytes=dom_size,
			element_count=element_count,
			**metadata
		)
		
		# Save snapshot metadata
		metadata_file = self.data_dir / "dom_snapshots" / f"{snapshot.snapshot_id}.json"
		with open(metadata_file, 'w') as f:
			json.dump(snapshot.model_dump(), f, indent=2, default=str)
			
		# Save DOM content separately (compressed)
		import gzip
		dom_file = self.data_dir / "dom_snapshots" / f"{snapshot.snapshot_id}.html.gz"
		with gzip.open(dom_file, 'wt') as f:
			f.write(dom_content)
			
		self.logger.info(f"Stored DOM snapshot: {snapshot.snapshot_id}")
		return snapshot.snapshot_id
		
	def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
		"""Retrieve a conversation by ID"""
		# Find conversation file (may have hash suffix)
		pattern = f"{conversation_id}_*.json"
		matching_files = list((self.data_dir / "conversations").glob(pattern))
		
		if not matching_files:
			return None
			
		with open(matching_files[0], 'r') as f:
			conversation_data = json.load(f)
			
		return ConversationRecord(**conversation_data)
		
	def get_dom_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
		"""Retrieve DOM snapshot with content"""
		metadata_file = self.data_dir / "dom_snapshots" / f"{snapshot_id}.json"
		dom_file = self.data_dir / "dom_snapshots" / f"{snapshot_id}.html.gz"
		
		if not metadata_file.exists() or not dom_file.exists():
			return None
			
		# Load metadata
		with open(metadata_file, 'r') as f:
			metadata = json.load(f)
			
		# Load DOM content
		import gzip
		with gzip.open(dom_file, 'rt') as f:
			dom_content = f.read()
			
		return {
			"metadata": DOMSnapshot(**metadata),
			"dom_content": dom_content
		}
		
	def list_conversations(
		self,
		date_from: Optional[datetime] = None,
		date_to: Optional[datetime] = None,
		model_id: Optional[str] = None,
		success_only: bool = False,
		min_quality_score: Optional[float] = None
	) -> List[ConversationRecord]:
		"""List conversations with filters"""
		conversations = []
		
		for conv_file in (self.data_dir / "conversations").glob("*.json"):
			with open(conv_file, 'r') as f:
				conv_data = json.load(f)
				
			conversation = ConversationRecord(**conv_data)
			
			# Apply filters
			if date_from and conversation.timestamp < date_from:
				continue
			if date_to and conversation.timestamp > date_to:
				continue
			if model_id and conversation.model_id != model_id:
				continue
			if success_only and not conversation.success:
				continue
			if min_quality_score and (conversation.quality_score or 0) < min_quality_score:
				continue
				
			conversations.append(conversation)
			
		return sorted(conversations, key=lambda x: x.timestamp, reverse=True)
		
	def create_data_version(
		self,
		version_name: str,
		created_by: str,
		description: Optional[str] = None,
		conversation_filters: Optional[Dict] = None,
		parent_version: Optional[str] = None
	) -> str:
		"""Create a new data version"""
		
		version_id = f"{version_name}_{int(datetime.now().timestamp())}"
		
		# Get conversations matching filters
		conversations = self.list_conversations(**(conversation_filters or {}))
		
		# Calculate statistics
		successful_conversations = [c for c in conversations if c.success]
		quality_scores = [c.quality_score for c in conversations if c.quality_score is not None]
		
		version = DataVersion(
			version_id=version_id,
			version_name=version_name,
			created_by=created_by,
			description=description,
			total_conversations=len(conversations),
			success_rate=len(successful_conversations) / len(conversations) if conversations else 0,
			avg_quality_score=sum(quality_scores) / len(quality_scores) if quality_scores else None,
			parent_version=parent_version
		)
		
		# Save version metadata
		version_file = self.data_dir / "versions" / f"{version_id}.json"
		with open(version_file, 'w') as f:
			json.dump(version.model_dump(), f, indent=2, default=str)
			
		# Create version directory and copy data
		version_dir = self.data_dir / "versions" / version_id
		version_dir.mkdir(exist_ok=True)
		
		(version_dir / "conversations").mkdir(exist_ok=True)
		(version_dir / "dom_snapshots").mkdir(exist_ok=True)
		
		# Copy conversation files
		for conversation in conversations:
			pattern = f"{conversation.conversation_id}_*.json"
			matching_files = list((self.data_dir / "conversations").glob(pattern))
			
			for source_file in matching_files:
				target_file = version_dir / "conversations" / source_file.name
				shutil.copy2(source_file, target_file)
				
		# Copy related DOM snapshots
		conversation_ids = {c.conversation_id for c in conversations}
		for snapshot_file in (self.data_dir / "dom_snapshots").glob("*.json"):
			with open(snapshot_file, 'r') as f:
				snapshot_data = json.load(f)
				
			if snapshot_data.get("conversation_id") in conversation_ids:
				# Copy both metadata and content files
				shutil.copy2(snapshot_file, version_dir / "dom_snapshots")
				
				content_file = snapshot_file.with_suffix(".html.gz")
				if content_file.exists():
					shutil.copy2(content_file, version_dir / "dom_snapshots")
					
		self.logger.info(f"Created data version: {version_id}")
		return version_id
		
	def load_data_version(self, version_id: str) -> Optional[DataVersion]:
		"""Load data version metadata"""
		version_file = self.data_dir / "versions" / f"{version_id}.json"
		
		if not version_file.exists():
			return None
			
		with open(version_file, 'r') as f:
			version_data = json.load(f)
			
		return DataVersion(**version_data)
		
	def list_data_versions(self) -> List[DataVersion]:
		"""List all data versions"""
		versions = []
		
		for version_file in (self.data_dir / "versions").glob("*.json"):
			with open(version_file, 'r') as f:
				version_data = json.load(f)
				
			versions.append(DataVersion(**version_data))
			
		return sorted(versions, key=lambda x: x.created_at, reverse=True)
		
	def export_training_data(
		self,
		version_id: str,
		output_dir: str,
		format: str = "json",
		include_dom_snapshots: bool = False
	):
		"""Export data version for training"""
		version_dir = self.data_dir / "versions" / version_id
		if not version_dir.exists():
			raise ValueError(f"Version {version_id} not found")
			
		output_path = Path(output_dir)
		output_path.mkdir(parents=True, exist_ok=True)
		
		# Load conversations
		conversations = []
		for conv_file in (version_dir / "conversations").glob("*.json"):
			with open(conv_file, 'r') as f:
				conv_data = json.load(f)
			conversations.append(conv_data)
			
		# Export in requested format
		if format == "json":
			output_file = output_path / f"{version_id}_training_data.json"
			with open(output_file, 'w') as f:
				json.dump({
					"version_id": version_id,
					"exported_at": datetime.now().isoformat(),
					"conversations": conversations,
					"total_conversations": len(conversations)
				}, f, indent=2, default=str)
				
		elif format == "jsonl":
			output_file = output_path / f"{version_id}_training_data.jsonl"
			with open(output_file, 'w') as f:
				for conv in conversations:
					f.write(json.dumps(conv, default=str) + '\n')
					
		elif format == "csv":
			import pandas as pd
			
			# Flatten conversation data for CSV
			flattened = []
			for conv in conversations:
				flat_conv = {
					"conversation_id": conv["conversation_id"],
					"timestamp": conv["timestamp"],
					"task_description": conv["task_description"],
					"success": conv.get("success"),
					"completion_time": conv.get("completion_time_seconds"),
					"steps_taken": conv.get("steps_taken", 0),
					"model_id": conv.get("model_id"),
					"quality_score": conv.get("quality_score"),
					"message_count": len(conv.get("messages", []))
				}
				flattened.append(flat_conv)
				
			df = pd.DataFrame(flattened)
			output_file = output_path / f"{version_id}_training_data.csv"
			df.to_csv(output_file, index=False)
			
		# Optionally include DOM snapshots
		if include_dom_snapshots:
			snapshots_dir = output_path / "dom_snapshots"
			shutil.copytree(
				version_dir / "dom_snapshots",
				snapshots_dir,
				dirs_exist_ok=True
			)
			
		self.logger.info(f"Exported training data to {output_path}")
		
	def calculate_data_quality_metrics(self, conversations: List[ConversationRecord]) -> Dict[str, Any]:
		"""Calculate data quality metrics for a set of conversations"""
		if not conversations:
			return {"error": "No conversations provided"}
			
		metrics = {
			"total_conversations": len(conversations),
			"success_rate": len([c for c in conversations if c.success]) / len(conversations),
			"avg_completion_time": sum(c.completion_time_seconds or 0 for c in conversations) / len(conversations),
			"avg_steps_taken": sum(c.steps_taken for c in conversations) / len(conversations),
			"error_rate": len([c for c in conversations if c.errors_encountered]) / len(conversations),
			"quality_distribution": {},
			"model_distribution": {},
			"category_distribution": {},
			"temporal_distribution": {}
		}
		
		# Quality score distribution
		quality_scores = [c.quality_score for c in conversations if c.quality_score is not None]
		if quality_scores:
			metrics["quality_distribution"] = {
				"mean": sum(quality_scores) / len(quality_scores),
				"min": min(quality_scores),
				"max": max(quality_scores),
				"count": len(quality_scores)
			}
			
		# Model distribution
		models = {}
		for conv in conversations:
			if conv.model_id:
				models[conv.model_id] = models.get(conv.model_id, 0) + 1
		metrics["model_distribution"] = models
		
		# Category distribution
		categories = {}
		for conv in conversations:
			if conv.task_category:
				categories[conv.task_category] = categories.get(conv.task_category, 0) + 1
		metrics["category_distribution"] = categories
		
		# Temporal distribution (by month)
		temporal = {}
		for conv in conversations:
			month_key = conv.timestamp.strftime("%Y-%m")
			temporal[month_key] = temporal.get(month_key, 0) + 1
		metrics["temporal_distribution"] = temporal
		
		return metrics
		
	def detect_data_drift(
		self,
		baseline_version: str,
		comparison_version: str
	) -> Dict[str, Any]:
		"""Detect data drift between two versions"""
		
		# Load both versions
		baseline = self.load_data_version(baseline_version)
		comparison = self.load_data_version(comparison_version)
		
		if not baseline or not comparison:
			raise ValueError("One or both versions not found")
			
		# Load conversations for both versions
		baseline_convs = self._load_version_conversations(baseline_version)
		comparison_convs = self._load_version_conversations(comparison_version)
		
		# Calculate metrics for both
		baseline_metrics = self.calculate_data_quality_metrics(baseline_convs)
		comparison_metrics = self.calculate_data_quality_metrics(comparison_convs)
		
		# Calculate drift
		drift_analysis = {
			"baseline_version": baseline_version,
			"comparison_version": comparison_version,
			"analysis_date": datetime.now().isoformat(),
			"drift_detected": False,
			"significant_changes": [],
			"metric_changes": {}
		}
		
		# Compare key metrics
		key_metrics = ["success_rate", "avg_completion_time", "avg_steps_taken", "error_rate"]
		
		for metric in key_metrics:
			baseline_val = baseline_metrics.get(metric, 0)
			comparison_val = comparison_metrics.get(metric, 0)
			
			if baseline_val > 0:
				change_pct = (comparison_val - baseline_val) / baseline_val * 100
			else:
				change_pct = 0
				
			drift_analysis["metric_changes"][metric] = {
				"baseline": baseline_val,
				"comparison": comparison_val,
				"change_percent": change_pct
			}
			
			# Flag significant changes (>10% change)
			if abs(change_pct) > 10:
				drift_analysis["significant_changes"].append({
					"metric": metric,
					"change_percent": change_pct,
					"direction": "increase" if change_pct > 0 else "decrease"
				})
				drift_analysis["drift_detected"] = True
				
		return drift_analysis
		
	def _load_version_conversations(self, version_id: str) -> List[ConversationRecord]:
		"""Helper to load conversations for a specific version"""
		version_dir = self.data_dir / "versions" / version_id / "conversations"
		conversations = []
		
		if not version_dir.exists():
			return conversations
			
		for conv_file in version_dir.glob("*.json"):
			with open(conv_file, 'r') as f:
				conv_data = json.load(f)
			conversations.append(ConversationRecord(**conv_data))
			
		return conversations
		
	def cleanup_old_data(self, retention_days: int = 90):
		"""Remove old conversation and snapshot data"""
		cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 3600)
		
		cleaned_conversations = 0
		cleaned_snapshots = 0
		
		# Clean old conversations
		for conv_file in (self.data_dir / "conversations").glob("*.json"):
			if conv_file.stat().st_mtime < cutoff_date:
				conv_file.unlink()
				cleaned_conversations += 1
				
		# Clean old DOM snapshots
		for snapshot_file in (self.data_dir / "dom_snapshots").glob("*.json"):
			if snapshot_file.stat().st_mtime < cutoff_date:
				# Remove both metadata and content files
				snapshot_file.unlink()
				
				content_file = snapshot_file.with_suffix(".html.gz")
				if content_file.exists():
					content_file.unlink()
					
				cleaned_snapshots += 1
				
		self.logger.info(f"Cleaned up {cleaned_conversations} conversations and {cleaned_snapshots} snapshots")
		
	def get_storage_stats(self) -> Dict[str, Any]:
		"""Get storage usage statistics"""
		stats = {
			"total_conversations": len(list((self.data_dir / "conversations").glob("*.json"))),
			"total_dom_snapshots": len(list((self.data_dir / "dom_snapshots").glob("*.json"))),
			"total_versions": len(list((self.data_dir / "versions").glob("*.json"))),
			"storage_usage_bytes": 0,
			"storage_by_type": {}
		}
		
		# Calculate storage usage
		for dir_name in ["conversations", "dom_snapshots", "versions"]:
			dir_path = self.data_dir / dir_name
			if dir_path.exists():
				size = sum(f.stat().st_size for f in dir_path.rglob("*") if f.is_file())
				stats["storage_by_type"][dir_name] = size
				stats["storage_usage_bytes"] += size
				
		return stats