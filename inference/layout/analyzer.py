"""
Layout analysis and extraction module.
Groups text blocks by spatial proximity and detects tables.
Uses rule-based heuristics for deterministic results.
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TextRegion:
    """Represents a logical region of text."""
    region_id: str
    text_blocks_indices: List[int]  # Indices into the original text blocks list
    region_type: str  # "header", "body", "table", "list", "form_field"
    bounding_box: Tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TableCell:
    """Represents a cell in detected table."""
    row_index: int
    col_index: int
    text: str
    confidence: float


@dataclass
class Table:
    """Represents a detected table structure."""
    table_id: str
    rows: int
    columns: int
    cells: List[TableCell]
    bounding_box: Tuple[int, int, int, int]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        cells_dict = [asdict(cell) for cell in self.cells]
        return {
            "table_id": self.table_id,
            "rows": self.rows,
            "columns": self.columns,
            "cells": cells_dict,
            "bounding_box": self.bounding_box
        }


@dataclass
class LayoutAnalysisResult:
    """Complete layout analysis output."""
    document_id: str
    regions: List[TextRegion]
    tables: List[Table]
    key_value_pairs: Dict[str, str]  # Detected key-value pairs
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "regions": [r.to_dict() for r in self.regions],
            "tables": [t.to_dict() for t in self.tables],
            "key_value_pairs": self.key_value_pairs
        }


class LayoutAnalyzer:
    """
    Analyzes document layout to extract structure.
    Groups text blocks and detects tables.
    """
    
    def __init__(
        self,
        proximity_threshold: int = 15,
        min_block_height: int = 10,
        min_block_width: int = 20,
        table_row_threshold: int = 10
    ):
        """
        Initialize layout analyzer.
        
        Args:
            proximity_threshold: Pixels between blocks to consider as same region
            min_block_height: Minimum height for text block
            min_block_width: Minimum width for text block
            table_row_threshold: Vertical gap threshold for table rows
        """
        self.proximity_threshold = proximity_threshold
        self.min_block_height = min_block_height
        self.min_block_width = min_block_width
        self.table_row_threshold = table_row_threshold
    
    def analyze(self, text_blocks: list) -> LayoutAnalysisResult:
        """
        Analyze layout of text blocks.
        
        Args:
            text_blocks: List of TextBlock objects from OCR
            
        Returns:
            LayoutAnalysisResult with regions, tables, and key-value pairs
        """
        # Filter valid blocks
        valid_blocks = [
            (i, block) for i, block in enumerate(text_blocks)
            if self._is_valid_block(block)
        ]
        
        if not valid_blocks:
            logger.warning("No valid text blocks found for layout analysis")
            return LayoutAnalysisResult(
                document_id="",
                regions=[],
                tables=[],
                key_value_pairs={}
            )
        
        # Group text blocks into regions
        regions = self._group_into_regions(valid_blocks)
        
        # Detect tables
        tables = self._detect_tables(valid_blocks)
        
        # Extract key-value pairs
        key_value_pairs = self._extract_key_value_pairs(valid_blocks)
        
        logger.info(
            f"Layout analysis complete: {len(regions)} regions, "
            f"{len(tables)} tables, {len(key_value_pairs)} key-value pairs"
        )
        
        return LayoutAnalysisResult(
            document_id="",
            regions=regions,
            tables=tables,
            key_value_pairs=key_value_pairs
        )
    
    def _is_valid_block(self, block) -> bool:
        """Check if text block meets minimum size requirements."""
        bbox = block.bbox
        width = bbox[2]  # width
        height = bbox[3]  # height
        
        return (
            width >= self.min_block_width and
            height >= self.min_block_height and
            block.text and
            block.confidence > 0.3
        )
    
    def _group_into_regions(self, blocks_with_indices: List[Tuple[int, object]]) -> List[TextRegion]:
        """
        Group text blocks into logical regions using spatial clustering.
        
        Args:
            blocks_with_indices: List of (index, TextBlock) tuples
            
        Returns:
            List of TextRegion objects
        """
        if not blocks_with_indices:
            return []
        
        # Sort by y coordinate (top to bottom)
        sorted_blocks = sorted(blocks_with_indices, key=lambda x: x[1].y_min)
        
        regions = []
        current_region_indices = []
        current_y_max = -1
        region_counter = 0
        
        for idx, block in sorted_blocks:
            # Start new region if vertical gap is large
            if current_region_indices and (block.y_min - current_y_max) > self.proximity_threshold:
                # Save current region
                bbox = self._compute_region_bbox(blocks_with_indices, current_region_indices)
                region = TextRegion(
                    region_id=f"region_{region_counter}",
                    text_blocks_indices=current_region_indices.copy(),
                    region_type="body",  # Default type
                    bounding_box=bbox
                )
                regions.append(region)
                region_counter += 1
                current_region_indices = []
                current_y_max = -1
            
            current_region_indices.append(idx)
            current_y_max = max(current_y_max, block.y_max)
        
        # Add final region
        if current_region_indices:
            bbox = self._compute_region_bbox(blocks_with_indices, current_region_indices)
            region = TextRegion(
                region_id=f"region_{region_counter}",
                text_blocks_indices=current_region_indices,
                region_type="body",
                bounding_box=bbox
            )
            regions.append(region)
        
        return regions
    
    def _compute_region_bbox(
        self,
        blocks_with_indices: List[Tuple[int, object]],
        indices: List[int]
    ) -> Tuple[int, int, int, int]:
        """Compute bounding box for a region."""
        if not indices:
            return (0, 0, 0, 0)
        
        blocks_in_region = [blocks_with_indices[i][1] for i in indices]
        
        x_min = min(b.x_min for b in blocks_in_region)
        y_min = min(b.y_min for b in blocks_in_region)
        x_max = max(b.x_max for b in blocks_in_region)
        y_max = max(b.y_max for b in blocks_in_region)
        
        return (x_min, y_min, x_max, y_max)
    
    def _detect_tables(self, blocks_with_indices: List[Tuple[int, object]]) -> List[Table]:
        """
        Detect tables in document using heuristics.
        Tables are characterized by aligned columns and rows.
        """
        if len(blocks_with_indices) < 4:
            return []
        
        tables = []
        
        # Extract coordinates
        blocks_info = [
            {
                'idx': idx,
                'block': block,
                'x_min': block.x_min,
                'x_max': block.x_max,
                'y_min': block.y_min,
                'y_max': block.y_max
            }
            for idx, block in blocks_with_indices
        ]
        
        # Find horizontally aligned blocks (potential table rows)
        y_positions = sorted(set(b['y_min'] for b in blocks_info))
        
        # Group blocks by row (similar y position)
        rows = []
        for y_pos in y_positions:
            row_blocks = [
                b for b in blocks_info
                if abs(b['y_min'] - y_pos) <= self.table_row_threshold
            ]
            if len(row_blocks) >= 3:  # Need at least 3 cells per row
                rows.append(row_blocks)
        
        # If we found multiple rows with similar structure, it's likely a table
        if len(rows) >= 2:
            # Calculate number of columns
            # Find x-aligned positions
            x_positions = defaultdict(list)
            for row in rows:
                for block in row:
                    x_center = (block['x_min'] + block['x_max']) / 2
                    # Find closest existing x position
                    found = False
                    for existing_x in list(x_positions.keys()):
                        if abs(x_center - existing_x) <= self.proximity_threshold:
                            x_positions[existing_x].append(block)
                            found = True
                            break
                    if not found:
                        x_positions[x_center].append(block)
            
            num_cols = len(x_positions)
            num_rows = len(rows)
            
            if num_cols >= 2 and num_rows >= 2:
                # Extract table cells
                cells = []
                for row_idx, row in enumerate(rows):
                    for col_idx, block in enumerate(row[:num_cols]):
                        cell = TableCell(
                            row_index=row_idx,
                            col_index=col_idx,
                            text=block['block'].text,
                            confidence=block['block'].confidence
                        )
                        cells.append(cell)
                
                # Compute table bbox
                all_x = [b['x_min'] for b in blocks_info] + [b['x_max'] for b in blocks_info]
                all_y = [b['y_min'] for b in blocks_info] + [b['y_max'] for b in blocks_info]
                table_bbox = (min(all_x), min(all_y), max(all_x), max(all_y))
                
                table = Table(
                    table_id="table_0",
                    rows=num_rows,
                    columns=num_cols,
                    cells=cells,
                    bounding_box=table_bbox
                )
                
                tables.append(table)
                logger.info(f"Detected table: {num_rows} rows x {num_cols} columns")
        
        return tables
    
    def _extract_key_value_pairs(self, blocks_with_indices: List[Tuple[int, object]]) -> Dict[str, str]:
        """
        Extract key-value pairs from form-like layouts.
        Heuristics: blocks on same line, separated by colon or whitespace.
        """
        key_value_pairs = {}
        
        # Group blocks by y position (same line)
        lines = defaultdict(list)
        for idx, block in blocks_with_indices:
            y_key = round(block.y_min / 10) * 10  # Group within 10 pixels
            lines[y_key].append((idx, block))
        
        # Process each line
        for y_key in sorted(lines.keys()):
            line_blocks = sorted(lines[y_key], key=lambda x: x[1].x_min)
            
            if len(line_blocks) >= 2:
                # Check for colon-separated pattern
                combined_text = " ".join(b[1].text for b in line_blocks)
                
                if ":" in combined_text:
                    parts = combined_text.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key and value:
                            key_value_pairs[key] = value
        
        return key_value_pairs
