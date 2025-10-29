"""
Lightweight text splitter - replaces langchain's RecursiveCharacterTextSplitter
"""
from typing import List


class RecursiveCharacterTextSplitter:
    """Split text into chunks recursively using multiple separators"""
    
    def __init__(
        self, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200,
        separators: List[str] = None,
        length_function=len
    ):
        """
        Initialize the text splitter.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to use for splitting (in priority order)
            length_function: Function to calculate text length (kept for compatibility)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        # Default separators in order of preference (similar to langchain)
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using recursive character splitting.
        
        Args:
            text: The text to split
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Try each separator in order
        final_chunks = []
        separator = self.separators[-1]
        new_separators = []
        
        for i, sep in enumerate(self.separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = self.separators[i + 1:]
                break
        
        # Split by the chosen separator
        splits = text.split(separator) if separator else list(text)
        
        # Now merge splits into chunks
        merged_chunks = self._merge_splits(splits, separator)
        
        # Recursively split chunks that are still too large
        for chunk in merged_chunks:
            if self.length_function(chunk) > self.chunk_size and new_separators:
                # Recursively split with remaining separators
                subsplitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=new_separators,
                    length_function=self.length_function
                )
                final_chunks.extend(subsplitter.split_text(chunk))
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _calculate_chunk_length(self, parts: List[str], separator_len: int) -> int:
        """
        Calculate the total length of a chunk with separators.
        
        Args:
            parts: List of text parts
            separator_len: Length of the separator
            
        Returns:
            Total length including separators
        """
        if not parts:
            return 0
        parts_length = sum(self.length_function(p) for p in parts)
        separators_length = separator_len * (len(parts) - 1)
        return parts_length + separators_length
    
    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """
        Merge splits into chunks of appropriate size.
        
        Args:
            splits: List of text splits
            separator: The separator used for splitting
            
        Returns:
            List of merged chunks
        """
        chunks = []
        current_chunk = []
        current_length = 0
        separator_len = self.length_function(separator)
        
        for split in splits:
            split_len = self.length_function(split)
            
            # If adding this split would exceed chunk_size, start a new chunk
            if current_length + split_len + (separator_len if current_chunk else 0) > self.chunk_size:
                if current_chunk:
                    # Save the current chunk
                    chunk_text = separator.join(current_chunk)
                    if chunk_text:
                        chunks.append(chunk_text)
                    
                    # Start new chunk with overlap
                    # Keep the last parts for overlap
                    overlap_text = separator.join(current_chunk)
                    if self.length_function(overlap_text) > self.chunk_overlap:
                        # Find where to start the overlap
                        overlap_parts = []
                        temp_len = 0
                        for part in reversed(current_chunk):
                            if temp_len + self.length_function(part) > self.chunk_overlap:
                                break
                            overlap_parts.insert(0, part)
                            temp_len += self.length_function(part) + separator_len
                        current_chunk = overlap_parts
                        # Calculate current length for overlap parts
                        current_length = self._calculate_chunk_length(
                            current_chunk, separator_len
                        )
                    else:
                        current_chunk = []
                        current_length = 0
            
            # Add the split to current chunk
            current_chunk.append(split)
            current_length += split_len + (separator_len if len(current_chunk) > 1 else 0)
        
        # Add the last chunk
        if current_chunk:
            chunk_text = separator.join(current_chunk)
            if chunk_text:
                chunks.append(chunk_text)
        
        return chunks
