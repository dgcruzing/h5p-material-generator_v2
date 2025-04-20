"""H5P package generation for H5P Material Generator."""

import json
import zipfile
import os
import uuid
import shutil
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import re

from h5p_generator.config import TEMP_DIR
from h5p_generator.utils import create_directory_if_not_exists


class H5PContentValidationException(ValueError):
    """Custom exception for H5P content validation errors."""

    pass


class H5PBuilder:
    """Builder for H5P packages."""

    def __init__(self, title: str, content_type: str = None):
        """
        Initialize H5P builder.

        Args:
            title: Title for the H5P package
            content_type: Type of content to generate (Multiple Choice, Fill in the Blanks, etc.)
        """
        self.title = title
        self.content_type = content_type
        self.library_source_dir = Path("content_types")
        self.temp_dir: Path = TEMP_DIR / f"h5p_{uuid.uuid4().hex}"
        self.content_dir: Path = self.temp_dir / "content"

    def __enter__(self):
        """Create temporary directories when entering context."""
        create_directory_if_not_exists(self.temp_dir)
        create_directory_if_not_exists(self.content_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary directories when exiting context."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_course_presentation(
        self, content_data: List[Dict[str, Any]], output_filename: str, num_slides: int
    ) -> Tuple[str, str]:
        """
        Create H5P Course Presentation package.

        Args:
            content_data: List of content items for slides
            output_filename: Output filename for H5P package
            num_slides: The total number of slides to generate.

        Returns:
            Tuple of (h5p_filename, markdown_filename)
        """
        # --- Validate Input Data --- Start
        try:
            self._validate_content_data(content_data)
        except H5PContentValidationException as e:
            # Re-raise or handle appropriately (e.g., log and raise ValueError)
            # For now, re-raise to propagate the specific error
            raise e
        # --- Validate Input Data --- End

        h5p_data = self._create_h5p_metadata()
        content_json = self._create_content_json(content_data, num_slides)

        # Write metadata and content files
        with open(self.temp_dir / "h5p.json", "w") as f:
            json.dump(h5p_data, f)

        with open(self.content_dir / "content.json", "w") as f:
            json.dump(content_json, f)

        # Create H5P package (zip file)
        with zipfile.ZipFile(output_filename, "w") as h5p_zip:
            h5p_zip.write(self.temp_dir / "h5p.json", "h5p.json")
            h5p_zip.write(self.content_dir / "content.json", "content/content.json")

            # Copy required libraries
            dependencies = h5p_data.get("preloadedDependencies", [])
            copied_folders = set()
            for dep in dependencies:
                lib_folder_path = self._find_library_folder(
                    dep["machineName"],
                    int(dep["majorVersion"])
                )
                if lib_folder_path and lib_folder_path.name not in copied_folders:
                    self._add_directory_to_zip(h5p_zip, lib_folder_path, lib_folder_path.name)
                    copied_folders.add(lib_folder_path.name)
                elif not lib_folder_path:
                    logging.warning(f"Could not find compatible library folder for {dep['machineName']} v{dep['majorVersion']}")

        # Generate markdown file
        md_filename = f"{os.path.splitext(output_filename)[0]}_Questions.md"
        self._generate_markdown(content_data, md_filename, num_slides)

        return output_filename, md_filename

    def _create_h5p_metadata(self) -> Dict[str, Any]:
        """Create H5P metadata."""
        return {
            "title": self.title,
            "mainLibrary": "H5P.CoursePresentation",
            "language": "en",
            "embedTypes": ["iframe"],
            "preloadedDependencies": [
                {"machineName": "H5P.CoursePresentation", "majorVersion": "1", "minorVersion": "26"},
                {"machineName": "H5P.MultiChoice", "majorVersion": "1", "minorVersion": "16"},
                {"machineName": "H5P.Blanks", "majorVersion": "1", "minorVersion": "14"},
                {"machineName": "H5P.TrueFalse", "majorVersion": "1", "minorVersion": "8"},
                {"machineName": "H5P.AdvancedText", "majorVersion": "1", "minorVersion": "1"},
                {"machineName": "H5P.Question", "majorVersion": "1", "minorVersion": "5"},
                {"machineName": "H5P.JoubelUI", "majorVersion": "1", "minorVersion": "3"},
                {"machineName": "H5P.Transition", "majorVersion": "1", "minorVersion": "0"},
                {"machineName": "H5P.FontIcons", "majorVersion": "1", "minorVersion": "0"},
            ],
        }

    def _create_content_json(
        self, content_data: List[Dict[str, Any]], num_slides: int
    ) -> Dict[str, Any]:
        """Create H5P content JSON."""
        slides = []

        # Create slides based on content type
        slide_generator = self._get_slide_generator()

        # Ensure we only process up to num_slides items from content_data
        for i, item in enumerate(content_data[:num_slides]):
            slide = slide_generator(item, i)
            slides.append(slide)

        # Pad with empty slides if needed
        while len(slides) < num_slides:
            i = len(slides)
            empty_item = self._get_empty_item(i)
            slide = slide_generator(empty_item, i)
            slides.append(slide)

        return {
            "presentation": {
                "slides": slides,
                "keywordListEnabled": True,
                "globalBackgroundSelector": {},
                "keywordListAlwaysShow": False,
                "keywordListAutoHide": False,
                "keywordListOpacity": 90,
            },
            "override": {
                "activeSurface": False,
                "hideSummarySlide": False,
                "summarySlideSolutionButton": True,
                "summarySlideRetryButton": True,
                "enablePrintButton": False,
                "social": {
                    "showFacebookShare": False,
                    "facebookShare": {
                        "url": "@currentpageurl",
                        "quote": "I scored @score out of @maxScore on a task at @currentpageurl.",
                    },
                    "showTwitterShare": False,
                    "twitterShare": {
                        "statement": "I scored @score out of @maxScore on a task at @currentpageurl.",
                        "url": "@currentpageurl",
                        "hashtags": "h5p, course",
                    },
                    "showGoogleShare": False,
                    "googleShareUrl": "@currentpageurl",
                },
            },
            "l10n": {
                "slide": "Slide",
                "score": "Score",
                "yourScore": "Your Score",
                "maxScore": "Max Score",
                "total": "Total",
                "totalScore": "Total Score",
                "showSolutions": "Show solutions",
                "retry": "Retry",
                "exportAnswers": "Export text",
                "hideKeywords": "Hide sidebar navigation menu",
                "showKeywords": "Show sidebar navigation menu",
                "fullscreen": "Fullscreen",
                "exitFullscreen": "Exit fullscreen",
                "prevSlide": "Previous slide",
                "nextSlide": "Next slide",
                "currentSlide": "Current slide",
                "lastSlide": "Last slide",
                "solutionModeTitle": "Exit solution mode",
                "solutionModeText": "Solution Mode",
                "summaryMultipleTaskText": "Multiple tasks",
                "scoreMessage": "You achieved:",
                "shareFacebook": "Share on Facebook",
                "shareTwitter": "Share on Twitter",
                "shareGoogle": "Share on Google+",
                "summary": "Summary",
                "solutionsButtonTitle": "Show comments",
            },
        }

    def _get_slide_generator(self):
        """Get appropriate slide generator function based on content type."""
        generators = {
            "Multiple Choice": self._create_multiple_choice_slide,
            "Fill in the Blanks": self._create_fill_in_blanks_slide,
            "True/False": self._create_true_false_slide,
            "Text": self._create_text_slide,
        }

        return generators.get(self.content_type, self._create_text_slide)

    def _get_empty_item(self, index: int) -> Dict[str, Any]:
        """Get empty content item for a given index."""
        empty_items = {
            "Multiple Choice": {
                "question": f"Question {index + 1}",
                "options": ["A", "B", "C", "D"],
                "correct": "A",
            },
            "Fill in the Blanks": {
                "text": f"Sentence {index + 1} ____.",
                "answer": "missing",
            },
            "True/False": {"question": f"Statement {index + 1}", "correct": True},
            "Text": {"text": f"Slide {index + 1} Content", "notes": "No speaker notes"},
        }

        return empty_items.get(self.content_type, {"text": f"Slide {index + 1}"})

    def _create_multiple_choice_slide(
        self, item: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """Create a multiple choice slide."""
        question = item.get("question", f"Question {index + 1}")
        options = item.get("options", ["A", "B", "C", "D"])
        correct = item.get("correct", options[0] if options else "")

        slide = {
            "elements": [
                {
                    "x": 5,
                    "y": 5,
                    "width": 90,
                    "height": 90,
                    "action": {
                        "library": "H5P.MultiChoice 1.16",
                        "params": {
                            "question": question,
                            "answers": [
                                {"text": opt, "correct": opt == correct}
                                for opt in options
                            ],
                            "behaviour": {
                                "enableRetry": True,
                                "enableSolutionsButton": True,
                                "singlePoint": False,
                                "showSolutions": True,
                            },
                            "l10n": {
                                "showSolutions": "Show solutions",
                                "retry": "Retry",
                            },
                        },
                        "subContentId": f"slide-{index + 1}-mc-{uuid.uuid4().hex[:8]}",
                    },
                }
            ],
            "title": f"Question {index + 1}",
            "slideBackgroundSelector": {},
        }

        return slide

    def _create_fill_in_blanks_slide(
        self, item: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """Create a fill in the blanks slide."""
        text = item.get("text", f"Sentence {index + 1} ____.")
        answer = item.get("answer", "missing")

        # Format text for H5P.Blanks
        formatted_text = text.replace("____", f"*{answer}*")

        slide = {
            "elements": [
                {
                    "x": 5,
                    "y": 5,
                    "width": 90,
                    "height": 90,
                    "action": {
                        "library": "H5P.Blanks 1.14",
                        "params": {
                            "text": formatted_text,
                            "behaviour": {
                                "enableRetry": True,
                                "enableSolutionsButton": True,
                                "showSolutions": True,
                            },
                        },
                        "subContentId": f"slide-{index + 1}-blanks-{uuid.uuid4().hex[:8]}",
                    },
                }
            ],
            "title": f"Sentence {index + 1}",
            "slideBackgroundSelector": {},
        }

        return slide

    def _create_true_false_slide(
        self, item: Dict[str, Any], index: int
    ) -> Dict[str, Any]:
        """Create a true/false slide."""
        question = item.get("question", f"Statement {index + 1}")
        correct_value = item.get("correct", True)

        # Convert string representation to boolean if needed
        if isinstance(correct_value, str):
            correct_value = correct_value.lower() == "true"

        slide = {
            "elements": [
                {
                    "x": 5,
                    "y": 5,
                    "width": 90,
                    "height": 90,
                    "action": {
                        "library": "H5P.TrueFalse 1.8",
                        "params": {
                            "question": question,
                            "correct": correct_value,
                            "behaviour": {
                                "enableRetry": True,
                                "enableSolutionsButton": True,
                                "showSolutions": True,
                            },
                        },
                        "subContentId": f"slide-{index + 1}-tf-{uuid.uuid4().hex[:8]}",
                    },
                }
            ],
            "title": f"Statement {index + 1}",
            "slideBackgroundSelector": {},
        }

        return slide

    def _create_text_slide(self, item: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a text slide."""
        # Handle different possible key names in item
        main_text = item.get("text", item.get("outline", f"Slide {index + 1} Content"))
        notes = item.get("notes", "No speaker notes provided.")

        slide = {
            "elements": [
                {
                    "x": 5,
                    "y": 5,
                    "width": 90,
                    "height": 40,
                    "action": {
                        "library": "H5P.AdvancedText 1.1",
                        "params": {"text": f"<h3>{main_text}</h3>"},
                        "subContentId": f"slide-{index + 1}-text-outline-{uuid.uuid4().hex[:8]}",
                    },
                },
                {
                    "x": 5,
                    "y": 50,
                    "width": 90,
                    "height": 40,
                    "action": {
                        "library": "H5P.AdvancedText 1.1",
                        "params": {"text": f"<p><em>Speaker Notes:</em> {notes}</p>"},
                        "subContentId": f"slide-{index + 1}-text-notes-{uuid.uuid4().hex[:8]}",
                    },
                },
            ],
            "title": f"Slide {index + 1}",
            "slideBackgroundSelector": {},
        }

        return slide

    def _generate_markdown(
        self, content_data: List[Dict[str, Any]], output_filename: str, num_slides: int
    ) -> str:
        """
        Generate Markdown summary of content.

        Args:
            content_data: List of content items
            output_filename: Output filename for Markdown file
            num_slides: The number of slides/items to include in the summary.

        Returns:
            Path to generated Markdown file
        """
        markdown_content = f"# {self.content_type} Questions and Answers\n\n"

        for i, item in enumerate(content_data[:num_slides], 1):
            if self.content_type == "Multiple Choice":
                markdown_content += self._generate_multiple_choice_markdown(item, i)
            elif self.content_type == "Fill in the Blanks":
                markdown_content += self._generate_fill_in_blanks_markdown(item, i)
            elif self.content_type == "True/False":
                markdown_content += self._generate_true_false_markdown(item, i)
            elif self.content_type == "Text":
                markdown_content += self._generate_text_markdown(item, i)

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return output_filename

    def _generate_multiple_choice_markdown(
        self, item: Dict[str, Any], index: int
    ) -> str:
        """Generate Markdown for multiple choice question."""
        question = item.get("question", f"Question {index}")
        options = item.get("options", [])
        correct = item.get("correct", "")

        md = f"## Question {index}: {question}\n"
        md += "Options:\n"

        for j, opt in enumerate(options, 1):
            marker = "*" if opt == correct else "-"
            md += f"  {marker} {j}. {opt}\n"

        md += f"**Correct Answer**: {correct}\n\n"
        return md

    def _generate_fill_in_blanks_markdown(
        self, item: Dict[str, Any], index: int
    ) -> str:
        """Generate Markdown for fill in the blanks question."""
        text = item.get("text", f"Sentence {index}")
        answer = item.get("answer", "")

        md = f"## Sentence {index}: {text}\n"
        md += f"**Answer**: {answer}\n\n"
        return md

    def _generate_true_false_markdown(self, item: Dict[str, Any], index: int) -> str:
        """Generate Markdown for true/false question."""
        question = item.get("question", f"Statement {index}")
        correct = item.get("correct", "")

        md = f"## Statement {index}: {question}\n"
        md += f"**Answer**: {correct}\n\n"
        return md

    def _generate_text_markdown(self, item: Dict[str, Any], index: int) -> str:
        """Generate Markdown for text slide."""
        main_text = item.get("text", item.get("outline", f"Slide {index} Content"))
        notes = item.get("notes", "No speaker notes provided.")

        md = f"## Slide {index}: {main_text}\n"
        md += f"**Speaker Notes**: {notes}\n\n"
        return md

    # --- Validation Methods --- START

    def _validate_multiple_choice_item(self, item: Dict[str, Any], index: int) -> None:
        """Validate structure for a Multiple Choice item."""
        if not isinstance(item.get("question"), str) or not item["question"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Missing or invalid 'question' (string expected)."
            )
        if not isinstance(item.get("options"), list) or len(item["options"]) == 0:
            raise H5PContentValidationException(
                f"Item {index + 1}: Missing or invalid 'options' (non-empty list expected)."
            )
        if not all(isinstance(opt, str) for opt in item["options"]):
            raise H5PContentValidationException(
                f"Item {index + 1}: Not all 'options' are strings."
            )
        if not isinstance(item.get("correct"), str) or not item["correct"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Missing or invalid 'correct' answer (string expected)."
            )
        if item["correct"] not in item["options"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Correct answer '{item['correct']}' not found in options."
            )

    def _validate_fill_in_blanks_item(self, item: Dict[str, Any], index: int) -> None:
        """Validate structure for a Fill in the Blanks item."""
        if not isinstance(item.get("text"), str) or not item["text"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Missing or invalid 'text' (string expected)."
            )
        if "____" not in item["text"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Text must contain '____' for the blank."
            )
        if not isinstance(item.get("answer"), str) or not item["answer"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Missing or invalid 'answer' (string expected)."
            )

    def _validate_true_false_item(self, item: Dict[str, Any], index: int) -> None:
        """Validate structure for a True/False item."""
        if not isinstance(item.get("question"), str) or not item["question"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Missing or invalid 'question' (string expected)."
            )
        # Allow boolean or string representations of boolean
        correct = item.get("correct")
        if not isinstance(correct, (bool, str)):
            raise H5PContentValidationException(
                f"Item {index + 1}: Missing or invalid 'correct' value (boolean or string 'true'/'false' expected)."
            )
        if isinstance(correct, str) and correct.lower() not in ["true", "false"]:
            raise H5PContentValidationException(
                f"Item {index + 1}: Invalid string value for 'correct' ('{correct}'). Use 'true' or 'false'."
            )

    def _validate_text_item(self, item: Dict[str, Any], index: int) -> None:
        """Validate structure for a Text item."""
        # Less strict, primarily needs a text field
        if not isinstance(item.get("text"), str) or not item["text"]:
            # Allow alternative key 'outline'
            if not isinstance(item.get("outline"), str) or not item["outline"]:
                raise H5PContentValidationException(
                    f"Item {index + 1}: Missing or invalid 'text' or 'outline' (string expected)."
                )

    def _validate_content_data(self, content_data: List[Dict[str, Any]]) -> None:
        """Validate the overall structure of the content data list based on content type."""
        if not content_data:
            raise H5PContentValidationException(
                "Received empty content data list from LLM."
            )

        validation_func_map = {
            "Multiple Choice": self._validate_multiple_choice_item,
            "Fill in the Blanks": self._validate_fill_in_blanks_item,
            "True/False": self._validate_true_false_item,
            "Text": self._validate_text_item,
        }

        validation_func = validation_func_map.get(self.content_type)

        if not validation_func:
            # Should not happen if content_type is from the dropdown, but good practice
            raise H5PContentValidationException(
                f"Unsupported content type for validation: {self.content_type}"
            )

        for i, item in enumerate(content_data):
            if not isinstance(item, dict):
                raise H5PContentValidationException(
                    f"Item {i + 1} is not a dictionary."
                )
            try:
                validation_func(item, i)
            except KeyError as e:
                # Catch potential KeyErrors if .get() wasn't used appropriately in validation func (shouldn't happen with current funcs)
                raise H5PContentValidationException(
                    f"Item {i + 1}: Missing required key {e}."
                )

    # --- Validation Methods --- END

    def _find_library_folder(self, machine_name: str, major_version: int) -> Optional[Path]:
        """Find the highest compatible library version folder."""
        best_match: Optional[Path] = None
        highest_minor_version = -1

        pattern = re.compile(rf"^{re.escape(machine_name)}-{major_version}\.(\d+)$")

        if not self.library_source_dir.exists():
            logging.error(f"Library source directory not found: {self.library_source_dir}")
            return None

        for item in self.library_source_dir.iterdir():
            if item.is_dir():
                match = pattern.match(item.name)
                if match:
                    minor_version = int(match.group(1))
                    if minor_version > highest_minor_version:
                        highest_minor_version = minor_version
                        best_match = item

        if best_match:
            logging.info(f"Found library folder for {machine_name} v{major_version}: {best_match.name}")
        else:
            logging.warning(f"No compatible folder found for {machine_name} v{major_version}")

        return best_match

    def _add_directory_to_zip(self, zip_file: zipfile.ZipFile, source_dir: Path, arc_dir: str):
        """Recursively add a directory to the zip file."""
        for item in source_dir.rglob("*"):
            file_path = item
            arc_path = os.path.join(arc_dir, item.relative_to(source_dir))
            if item.is_file():
                 zip_file.write(file_path, arc_path)
            elif item.is_dir():
                 # Usually directories are created implicitly when files are added
                 # but ensure empty directories are added if necessary (though unlikely needed for H5P)
                 # zip_file.write(file_path, arc_path)
                 pass # Typically not needed
