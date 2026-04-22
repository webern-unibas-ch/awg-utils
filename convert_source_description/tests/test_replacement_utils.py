"""Tests for replacement_utils.py"""

from utils.replacement_utils import ReplacementUtils


class TestAddReportFragmentLinks:
    """Tests for the add_report_fragment_links function."""

    def test_add_simple_fragment_link(self):
        """Test adding a simple report fragment link."""
        input_text = "<strong>A</strong>"
        expected_output = (
            '<a (click)="ref.navigateToReportFragment('
            "{complexId: 'TODO', fragmentId: 'source_A'}"
            ')"><strong>A</strong></a>'
        )
        assert ReplacementUtils.add_report_fragment_links(input_text) == expected_output

    def test_add_multiple_fragment_links(self):
        """Test adding multiple report fragment links."""
        input_text = "<strong>A</strong> and <strong>B</strong>"
        expected_output = (
            '<a (click)="ref.navigateToReportFragment('
            "{complexId: 'TODO', fragmentId: 'source_A'}"
            ')"><strong>A</strong></a> and '
            '<a (click)="ref.navigateToReportFragment('
            "{complexId: 'TODO', fragmentId: 'source_B'}"
            ')"><strong>B</strong></a>'
        )
        assert ReplacementUtils.add_report_fragment_links(input_text) == expected_output

    def test_no_strong_tags(self):
        """Test text with no strong tags."""
        input_text = "This text has no strong tags"
        expected_output = "This text has no strong tags"
        assert ReplacementUtils.add_report_fragment_links(input_text) == expected_output


class TestEscapeCurlyBrackets:
    """Tests for the escape_curly_brackets function."""

    def test_escape_single_curly_brackets(self):
        """Test escaping single curly brackets."""
        input_text = "This {text} has curly brackets"
        expected_output = "This {{ '{' }}text{{ '}' }} has curly brackets"
        assert ReplacementUtils.escape_curly_brackets(input_text) == expected_output

    def test_escape_multiple_curly_brackets(self):
        """Test escaping multiple curly brackets."""
        input_text = "{open} and {close}"
        expected_output = "{{ '{' }}open{{ '}' }} and {{ '{' }}close{{ '}' }}"
        assert ReplacementUtils.escape_curly_brackets(input_text) == expected_output

    def test_no_curly_brackets(self):
        """Test text with no curly brackets."""
        input_text = "This text has no special characters"
        expected_output = "This text has no special characters"
        assert ReplacementUtils.escape_curly_brackets(input_text) == expected_output


class TestReplaceGlyphs:
    """Tests for the replace_glyphs function."""

    def test_glyphs_without_additional_class(self):
        """Test with glyphs that do not require an additional class."""
        input_text = "[f] [ff] [fff] [mp] [ped]"
        expected_output = (
            "<span class='glyph'>{{ref.getGlyph('f')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('ff')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('fff')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('mp')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('ped')}}</span>"
        )
        assert ReplacementUtils.replace_glyphs(input_text) == expected_output

    def test_with_accid_glyphs(self):
        """Test with glyphs that require the 'accid' class."""
        input_text = "[a] [b] [bb] [#] [x]"
        expected_output = (
            "<span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('b')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('bb')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('#')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('x')}}</span>"
        )
        assert ReplacementUtils.replace_glyphs(input_text) == expected_output

    def test_with_note_glyphs(self):
        """Test with glyphs that require the 'note' class."""
        input_text = (
            "[Achtelnote] [Ganze Note] [Halbe Note] [Punktierte Halbe Note] "
            "[Sechzehntelnote] [Viertelnote]"
        )
        expected_output = (
            "<span class='glyph note'>{{ref.getGlyph('Achtelnote')}}</span> "
            "<span class='glyph note'>{{ref.getGlyph('Ganze Note')}}</span> "
            "<span class='glyph note'>{{ref.getGlyph('Halbe Note')}}</span> "
            "<span class='glyph note'>{{ref.getGlyph('Punktierte Halbe Note')}}</span> "
            "<span class='glyph note'>{{ref.getGlyph('Sechzehntelnote')}}</span> "
            "<span class='glyph note'>{{ref.getGlyph('Viertelnote')}}</span>"
        )
        assert ReplacementUtils.replace_glyphs(input_text) == expected_output

    def test_with_mixed_glyphs(self):
        """Test with a mix of accid and non-accid glyphs."""
        input_text = "[a] [f] [bb] [mp] [#] [Achtelnote]"
        expected_output = (
            "<span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('f')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('bb')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('mp')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('#')}}</span> "
            "<span class='glyph note'>{{ref.getGlyph('Achtelnote')}}</span>"
        )
        assert ReplacementUtils.replace_glyphs(input_text) == expected_output

    def test_with_partial_matches(self):
        """Test with text containing partial matches."""
        input_text = (
            "This is a test string [a] with some glyphs [abc] [b] [bb] [#] [xylophone]"
        )
        expected_output = (
            "This is a test string <span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "with some glyphs [abc] <span class='glyph accid'>{{ref.getGlyph('b')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('bb')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('#')}}</span> [xylophone]"
        )
        assert ReplacementUtils.replace_glyphs(input_text) == expected_output

    def test_with_hyphen_exclusion(self):
        """Test that glyphs followed by a hyphen are not replaced."""
        input_text = "[a] [b] [bb-] [#-] [x]"
        expected_output = (
            "<span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('b')}}</span> [bb-] [#-] "
            "<span class='glyph accid'>{{ref.getGlyph('x')}}</span>"
        )
        assert ReplacementUtils.replace_glyphs(input_text) == expected_output

    def test_with_no_glyphs(self):
        """Test with text that contains no glyphs."""
        input_text = "This is a test string with no glyphs."
        expected_output = "This is a test string with no glyphs."
        assert ReplacementUtils.replace_glyphs(input_text) == expected_output

    def test_with_empty_string(self):
        """Test that an empty string is returned as an empty string."""
        # Arrange
        input_string = ""
        expected_result = ""
        # Act
        actual_result = ReplacementUtils.replace_glyphs(input_string)
        # Assert
        assert actual_result == expected_result
