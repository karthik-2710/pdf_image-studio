import os
import shutil
import tempfile
import unittest
from PIL import Image, ImageDraw

from core.file_manager import (
    get_image_metadata,
    get_pdf_metadata,
    generate_image_thumbnail,
    generate_pdf_page_thumbnail,
    safe_rename_file,
    generate_batch_rename_plan,
    apply_batch_rename,
    safe_delete_file,
    is_valid_image_file,
    is_valid_pdf_file,
    apply_image_adjustments,
    rotate_image_file_on_disk,
    save_image_to_disk,
    load_image_with_exif
)
from core.img_to_pdf import (
    convert_images_to_single_pdf,
    convert_images_to_individual_pdfs
)
from core.pdf_to_img import (
    convert_pdf_to_images,
    parse_page_range
)


class TestImagePdfStudioCore(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="studio_test_")
        self.img1_path = os.path.join(self.test_dir, "test1.png")
        self.img2_path = os.path.join(self.test_dir, "test2.jpg")
        self.img3_path = os.path.join(self.test_dir, "test3.png")

        # Create Image 1 (PNG, 400x300 red with text)
        im1 = Image.new("RGB", (400, 300), color=(220, 50, 50))
        d1 = ImageDraw.Draw(im1)
        d1.rectangle([20, 20, 380, 280], outline=(255, 255, 255), width=4)
        im1.save(self.img1_path)

        # Create Image 2 (JPG, 300x500 blue)
        im2 = Image.new("RGB", (300, 500), color=(50, 100, 220))
        im2.save(self.img2_path, "JPEG")

        # Create Image 3 (RGBA transparent, 200x200 green circle)
        im3 = Image.new("RGBA", (200, 200), color=(0, 0, 0, 0))
        d3 = ImageDraw.Draw(im3)
        d3.ellipse([10, 10, 190, 190], fill=(50, 200, 100, 200))
        im3.save(self.img3_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_manager_validation_and_metadata(self):
        self.assertTrue(is_valid_image_file(self.img1_path))
        self.assertTrue(is_valid_image_file(self.img2_path))
        self.assertFalse(is_valid_pdf_file(self.img1_path))

        meta = get_image_metadata(self.img1_path)
        self.assertEqual(meta["width"], 400)
        self.assertEqual(meta["height"], 300)
        self.assertEqual(meta["filename"], "test1.png")
        self.assertIn("KB", meta["size_formatted"])

    def test_thumbnail_generation(self):
        thumb = generate_image_thumbnail(self.img1_path, max_size=(80, 80))
        self.assertIsNotNone(thumb)
        self.assertLessEqual(thumb.width, 80)
        self.assertLessEqual(thumb.height, 80)

    def test_img_to_pdf_conversion(self):
        out_pdf = os.path.join(self.test_dir, "combined_output.pdf")
        res = convert_images_to_single_pdf(
            image_paths=[self.img1_path, self.img2_path, self.img3_path],
            output_pdf_path=out_pdf,
            page_size="a4",
            orientation="auto",
            margin="small",
            quality="high"
        )
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(out_pdf))
        self.assertEqual(res["pages_count"], 3)

        pdf_meta = get_pdf_metadata(out_pdf)
        self.assertEqual(pdf_meta["page_count"], 3)

        pdf_thumb = generate_pdf_page_thumbnail(out_pdf, page_number=0, max_size=(100, 100))
        self.assertIsNotNone(pdf_thumb)

    def test_extreme_compression(self):
        # Create a large high-res image
        large_img_path = os.path.join(self.test_dir, "large.png")
        large_img = Image.new("RGB", (3000, 2000), color=(100, 150, 200))
        large_img.save(large_img_path)

        out_normal = os.path.join(self.test_dir, "pdf_normal.pdf")
        convert_images_to_single_pdf(
            image_paths=[large_img_path],
            output_pdf_path=out_normal,
            quality="high"
        )

        out_extreme = os.path.join(self.test_dir, "pdf_extreme.pdf")
        convert_images_to_single_pdf(
            image_paths=[large_img_path],
            output_pdf_path=out_extreme,
            quality="extreme"
        )

        out_ultra = os.path.join(self.test_dir, "pdf_ultra.pdf")
        convert_images_to_single_pdf(
            image_paths=[large_img_path],
            output_pdf_path=out_ultra,
            quality="ultra_extreme"
        )

        size_normal = os.path.getsize(out_normal)
        size_extreme = os.path.getsize(out_extreme)
        size_ultra = os.path.getsize(out_ultra)

        self.assertLess(size_extreme, size_normal)
        self.assertLess(size_ultra, size_extreme)

    def test_pdf_to_img_conversion(self):
        # First generate a 3-page PDF
        pdf_path = os.path.join(self.test_dir, "source.pdf")
        convert_images_to_single_pdf(
            image_paths=[self.img1_path, self.img2_path, self.img3_path],
            output_pdf_path=pdf_path
        )

        out_img_dir = os.path.join(self.test_dir, "extracted_images")
        res = convert_pdf_to_images(
            pdf_path=pdf_path,
            output_directory=out_img_dir,
            image_format="png",
            dpi=150,
            page_range_str="1, 3"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["converted_count"], 2)
        self.assertEqual(len(res["files"]), 2)
        for f in res["files"]:
            self.assertTrue(os.path.exists(f))

    def test_page_range_parser(self):
        # Range string tests
        self.assertEqual(parse_page_range("1-3, 5", 10), [0, 1, 2, 4])
        self.assertEqual(parse_page_range("odd", 6), [0, 2, 4])
        self.assertEqual(parse_page_range("even", 6), [1, 3, 5])
        self.assertEqual(parse_page_range("all", 4), [0, 1, 2, 3])

    def test_batch_and_single_renaming(self):
        # Single safe rename
        new_path = safe_rename_file(self.img1_path, "renamed_pic.png")
        self.assertTrue(os.path.exists(new_path))
        self.assertFalse(os.path.exists(self.img1_path))
        self.img1_path = new_path

        # Batch rename preview
        plan = generate_batch_rename_plan(
            file_paths=[self.img1_path, self.img2_path],
            pattern_mode="numbering",
            prefix="photo",
            start_number=1,
            digits_padding=2
        )
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["new_name"], "photo_01.png")
        self.assertEqual(plan[1]["new_name"], "photo_02.jpg")

        # Apply batch rename
        results = apply_batch_rename(plan)
        for r in results:
            self.assertTrue(r["success"])
            self.assertTrue(os.path.exists(r["new_path"]))

    def test_safe_delete(self):
        self.assertTrue(os.path.exists(self.img3_path))
        deleted = safe_delete_file(self.img3_path)
        self.assertTrue(deleted)
        self.assertFalse(os.path.exists(self.img3_path))

    def test_image_rotation_and_adjustments(self):
        # 1. Test in-memory adjustments
        with Image.open(self.img1_path) as im:
            orig_w, orig_h = im.size  # 400x300
            
            # Rotate 90 degrees
            rot90 = apply_image_adjustments(im, rotation=90)
            self.assertEqual(rot90.size, (300, 400))

            # Crop box
            cropped = apply_image_adjustments(im, crop_box=(50, 50, 200, 150))
            self.assertEqual(cropped.size, (150, 100))

            # Filter grayscale
            gray = apply_image_adjustments(im, filter_mode="grayscale")
            self.assertEqual(gray.mode, "RGB")

            # Document scan filter
            doc_scan = apply_image_adjustments(im, filter_mode="document_scan")
            self.assertEqual(doc_scan.mode, "RGB")

        # 2. Test disk rotation
        rotate_image_file_on_disk(self.img1_path, 90)
        meta = get_image_metadata(self.img1_path)
        self.assertEqual(meta["width"], 300)
        self.assertEqual(meta["height"], 400)


if __name__ == "__main__":
    unittest.main()
