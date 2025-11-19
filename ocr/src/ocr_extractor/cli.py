"""Command-line interface for OCR Extractor."""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from .config import settings
from .extractor import (
    PDFTextExtractor,
    extract_text_from_images_batch,
    get_images_from_directory,
)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config_file: Optional[str]) -> None:
    """OCR Extractor - PDF to text extraction pipeline."""
    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj["settings"] = settings


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o", default=None, help="Directory to save extracted images"
)
@click.option(
    "--output-file", "-f", default=None, help="Output markdown file for extracted text"
)
@click.option(
    "--reconstruct",
    "-r",
    is_flag=True,
    help="Automatically reconstruct the document after extraction",
)
@click.pass_context
def extract_pdf(
    ctx: click.Context,
    pdf_path: str,
    output_dir: Optional[str],
    output_file: Optional[str],
    reconstruct: bool,
) -> None:
    """Extract text from a PDF file."""
    try:
        extractor = PDFTextExtractor()
        results = extractor.process_pdf(pdf_path, output_dir, output_file)

        if reconstruct:
            click.echo("🔄 Reconstructing document...")
            # Construct the full text exactly as it was saved
            full_text = "# Extracted Text from PDF\n\n"
            full_text += f"Total pages processed: {len(results)}\n\n"
            for i, (image_path, text) in enumerate(results.items(), 1):
                full_text += f"## Page {i}: {Path(image_path).name}\n\n"
                full_text += text
                full_text += "\n\n---\n\n"

            reconstructed_text = extractor.reconstruct_document(full_text)

            # Determine output file for reconstruction
            base_output = output_file or settings.default_output_file
            # Default to .docx for reconstruction
            recon_output = str(
                Path(base_output).with_name(f"reconstructed_{Path(base_output).stem}.docx")
            )

            extractor.save_to_docx(reconstructed_text, recon_output)
            click.echo(f"✅ Reconstructed document saved to {recon_output}")

        click.echo("✅ PDF processing complete!")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("image_paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    help="Directory containing images to process",
)
@click.option(
    "--output-file", "-f", default=None, help="Output markdown file for extracted text"
)
@click.pass_context
def extract_images(
    ctx: click.Context,
    image_paths: tuple,
    directory: Optional[str],
    output_file: Optional[str],
) -> None:
    """Extract text from image files."""
    try:
        if directory:
            images = get_images_from_directory(directory)
        elif image_paths:
            images = list(image_paths)
        else:
            # Default to img directory
            images = get_images_from_directory()

        if not images:
            click.echo("❌ No images found!", err=True)
            sys.exit(1)

        click.echo(f"Found {len(images)} image(s) to process")

        results = extract_text_from_images_batch(images)

        # Save results
        extractor = PDFTextExtractor()
        extractor.save_results(results, output_file)

        click.echo("✅ Image processing complete!")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "--output-dir", "-o", default=None, help="Directory to save extracted images"
)
@click.pass_context
def extract_images_only(
    ctx: click.Context, pdf_path: str, output_dir: Optional[str]
) -> None:
    """Extract images from PDF without OCR."""
    try:
        extractor = PDFTextExtractor()
        images = extractor.extract_images_from_pdf(pdf_path, output_dir)
        click.echo(
            f"✅ Extracted {len(images)} images to {output_dir or settings.output_dir}"
        )
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-file",
    "-o",
    default="reconstructed_document.docx",
    help="Output file for reconstructed text (supports .md and .docx)",
)
@click.pass_context
def reconstruct(ctx: click.Context, input_file: str, output_file: str) -> None:
    """Reconstruct a complete document from extracted text."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()

        click.echo("🔄 Reconstructing document...")
        extractor = PDFTextExtractor()
        reconstructed_text = extractor.reconstruct_document(text)

        if output_file.endswith(".docx"):
            extractor.save_to_docx(reconstructed_text, output_file)
        else:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(reconstructed_text)

        click.echo(f"✅ Document reconstructed to {output_file}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
