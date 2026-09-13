# ⚡ Image & PDF Converter Studio

A fast, modern, and easy-to-use desktop application to convert **Images to PDF** and **PDF to Images** with an interactive GUI, live thumbnail previews, page reordering, batch renaming, and safe file management.

---

## 🌟 Key Features

### 🖼️ Images to PDF Converter
- **Multi-Format Support**: JPG, JPEG, PNG, WEBP, BMP, TIFF, GIF, and more.
- **Windows Orientation Parity**: Automatically evaluates and respects EXIF orientation tags from Windows File Explorer and phone cameras.
- **1-Click In-App Rotation (`↺` / `↻`)**: Quick-rotate any individual image or batch rotate selected images directly from the card and toolbar, updating thumbnails and files on disk.
- **In-App Image Editor (`🎨 Edit`)**:
  - Rotate (90° CCW, 90° CW, 180°) and Flip (Horizontal / Vertical).
  - Crop / Trim margins with interactive sliders.
  - Brightness, Contrast, and Sharpness enhancement sliders.
  - Document Scan / High-Contrast Black & White filter for crisp text documents and receipts.
  - **Save & Overwrite Original File** (reflects directly in your Windows folders) or **Save as New Copy**.
- **Visual Image Queue**: High-resolution thumbnails with image resolution, color mode, and file size badges.
- **Drag & Reorder**: Move pages up/down (`▲`/`▼`), reverse order, or sort alphabetically/by date/by size.
- **Preview Inspector (`👁`)**: View full-resolution previews with EXIF parity, metadata, and quick rotate/edit tools.
- **Rename Options (`✏️`)**:
  - In-place single file renaming on disk.
  - Powerful **Batch Rename (`🏷`)** tool with Sequential Numbering (`img_001.jpg`), Prefix/Suffix, Find & Replace, and real-time preview table.
- **Queue & File Management**:
  - Remove from queue (`✕`) non-destructively.
  - Permanently delete from disk (`🗑️`) with confirmation dialog.
- **Page Layout Options**:
  - **Page Sizes**: Fit to Image (Original Pixels), A4, US Letter, A3, A5.
  - **Orientation**: Auto (Matches image aspect ratio), Portrait, Landscape.
  - **Margins**: None (Edge-to-Edge), Small (0.25 in), Normal (0.5 in), Large (0.75 in).
  - **Quality / Compression**:
    - **Extreme Compression (80-95% Smaller)**: Smart Lanczos downsampling (1600px max) + JPEG 38 + Progressive chroma subsampling + PDF stream deflation. Retains clear, readable text and crisp images while producing tiny PDFs.
    - **Ultra Compact / Email**: Maximum compression (1200px max, JPEG 28) for the smallest possible file sizes.
    - **High Quality (JPEG 90)** / **Medium (JPEG 75)** / **Low (JPEG 50)**.
    - **Lossless (Original / PNG)**.
  - **Max Image Resolution / Downscaling**: Auto, Full HD (1920px), Compact (1600px), Mobile/Web (1280px), Ultra Small (1024px), or Original Pixels.
- **Single or Batch Mode**: Combine all images into a single PDF or export each image as an individual PDF.

### 📄 PDF to Images Converter
- **Visual Page Browser**: Displays live rendered thumbnails for every single page in the PDF document.
- **Selective Page Conversion**:
  - Check/uncheck individual pages visually.
  - Quick buttons: "All Pages", "Deselect All", "Odd Pages Only", "Even Pages Only".
  - Custom page range syntax: `1-5, 8, 11-14`.
- **High-Fidelity Rendering Presets**:
  - 300 DPI (High Resolution / Print Quality)
  - 150 DPI (Standard Screen Quality)
  - 200 DPI (Crisp Presentation)
  - 72 DPI (Web Draft / Compact Size)
  - 600 DPI (Ultra Sharp)
- **Output Formats**: PNG (Lossless), JPG (Custom Quality Slider), WEBP, TIFF, BMP.
- **Custom Naming Template**: Customize output filename pattern (e.g. `{pdf_name}_page_{page:03d}`).

---

## 🚀 How to Run

### Method 1: Double Click (Windows)
Double click `run_app.bat` inside the `pdf-image-studio` folder.

### Method 2: Command Line
```bash
cd c:\Users\karthi\Documents\proji\pdf-image-studio
python main.py
```

---

## 📦 Requirements

- Python 3.10+
- Dependencies:
  ```bash
  pip install -r requirements.txt
  ```
  *(Packages: `customtkinter`, `pymupdf`, `Pillow`, `img2pdf`)*

---

## 🏗 Architecture

```
pdf-image-studio/
├── main.py                       # Application Entry Point
├── run_app.bat                   # 1-Click Windows Launcher
├── requirements.txt              # Python Dependencies
├── core/
│   ├── file_manager.py           # Metadata, Thumbnail cache, Safe Rename, Batch Rename, Delete
│   ├── img_to_pdf.py             # Image to PDF Conversion Engine
│   └── pdf_to_img.py             # PDF to Images Rendering Engine
├── gui/
│   ├── app.py                    # Main Window, Sidebar, Dark/Light Theme Handler
│   ├── img_to_pdf_tab.py         # Images -> PDF Workspace & Queue UI
│   ├── pdf_to_img_tab.py         # PDF -> Images Workspace & Page Browser UI
│   └── components/
│       ├── item_card.py          # Interactive Thumbnail Card with Quick Action Buttons
│       ├── preview_modal.py      # High-Resolution Full Viewer Inspector
│       └── rename_modal.py       # Single & Batch Rename Dialog with Live Preview
└── tests/
    └── test_conversion.py        # Automated Unit & Integration Tests
```
