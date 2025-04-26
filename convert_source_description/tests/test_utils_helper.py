# pylint: disable=protected-access
"""Tests for utils_helper.py"""

import pytest
from bs4 import BeautifulSoup, Tag
from utils_helper import ConversionUtilsHelper


@pytest.fixture(name='helper')
def fixture_helper():
    """Return an instance of ConversionUtilsHelper."""
    return ConversionUtilsHelper()


@pytest.fixture(name="sample_soup")
def fixture_sample_soup():
    """Return a sample BeautifulSoup object as fixture."""
    html = """
    <html>
        <head>
            <title>Test File</title>
        </head>
        <body>
            <p><strong>Studienkomposition für Klavier / Streichquartett M 22</strong></p>
            <p><strong>A</strong></p>
            <p>Skizzen zu &lt;br /&gt;&lt;span class=\"tab\"&gt;&lt;/span&gt;Studienkomposition für Klavier / Streichquartett M 22.&lt;br /&gt;Enthält auch Skizzen zu Studienkomposition für Klavier M* 411–412 sowie Tintenniederschrift von Studienkomposition für Streichquartett M* 408. </p>
            <p>CH-Bps, Sammlung Anton Webern.</p>
            <p>1 Blatt: Das Blatt ist Bestandteil (Bl. 4) eines größeren Konvolutes bestehend aus 1 Blatt (Bl. 1), 1 Bogen (Bl. 2/3) und 1 Blatt (Bl. 4). Horizontale Knickfalte. Stockflecken unten mittig-rechts. Ecke unten links abgerissen (inkl. Firmenzeichen auf 1<sup>r</sup>). Rissspuren am linken Rand: von Bogen abgetrennt.</p>
            <p>Beschreibstoff: Notenpapier, 28 Systeme, Format: hoch 343 × 264 mm, Firmenzeichen abgerissen;</p><p>Notenpapier, 12 Systeme (unten beschnitten), Format (quer): 163 × 255 mm, kein Firmenzeichen. </p>
            <p>Schreibstoff: schwarze Tinte; Bleistift.</p>
            <p>Inhalt: </p>
            <p><strong>M* 408 </strong>(Tintenniederschrift von Studienkomposition für Klavier M* 408):</p>
            <p>Bl. 1<sup>r</sup>    System 2–5: T. 1–9;</p>
            <p>System 7–10: T. 10–17;</p>
            <p>System 12–15: T. 18–25;</p>
            <p>System 17–20:  T. 26–32.</p>
            <p><strong>M 22 Sk1 </strong>(Skizze zu Studienkomposition für Klavier M 22: Thema):</p>
            <p>Bl. 1<sup>r</sup>    System 22–23: T. 1–8.</p>

            <p><strong>B</strong></p>
            <p>Reihentabelle und Skizze op19.</p>
            <p>CH-Bps, Sammlung Anton Webern.</p>
            <p>1 Blatt. Rissspuren am rechten Rand: von Bogen abgetrennt und beschnitten. Abriss an der oberen rechten Ecke. Zwei Risse am rechten Rand. Archivalische Paginierung <em>[1]</em> bis <em>[2]</em> unten links oder rechts. Bl. 1<sup>v</sup> bis auf die archivalische Paginierung unbeschriftet. </p>
            <p>Beschreibstoff: Notenpapier, 12 Systeme (unten beschnitten), Format (quer): 163 × 255 mm, kein Firmenzeichen. </p>
            <p>Schreibstoff: Bleistift; blauer Buntstift, grüner Buntstift, roter Buntstift, Kopierstift.</p>
            <p>Titel: <em>Reihen zu op. 19 | 2 Lieder für gem Chor</em> auf Bl. 1<sup>r</sup> oben halbrechts mit blauem Buntstift, Punkt von <em>i</em> bei <em>Lieder</em> mit rotem Buntstift. </p>
            <p>Datierung: <em>1925/26</em> auf Bl. 1<sup>r</sup> oben rechts mit rotem Buntstift.</p>       
            <p>Paginierung: <em>[1]</em> bis <em>[2]</em> unten links oder rechts.</p>
            <p>Taktzahlen: <em>1</em> bis <em>16</em> auf Bl. 1<sup>r</sup> oben links mit grünem Buntstift.</p>
            <p>Besetzung: Klavier.</p>
            <p>Eintragungen: <em>Studienkomposition für Klavier / Streichquartett M 22</em></p>
            <p>Inhalt: </p>
            <p><strong>M 286 Sk#</strong> / <strong>M 287 Sk#</strong> (Reihentabelle op. 19): </p>
            <p>     Bl. 1<sup>r</sup>       System 1a: G<sub>g</sub> (1);   System 1b: K<sub>c</sub> (2); </p>
            <p>             System 2a: U<sub>g</sub> (3);   System 2b: KU<sub>d</sub> (4); </p>
            <p>             System 4a: G<sub>cis</sub> (5);         System 4b: K<sub>ges</sub> (6); </p>    
            <p>             System 5a: U<sub>cis</sub> (7);         System 5b: KU<sub>gis</sub> (8). </p>   
            <p><strong>M 286 Sk# </strong> (Skizze zu M 286):</p>
            <p>     Bl. 1<sup>r</sup>       System 8–9 (rechts): T. 15. </p>
            <p>     Bl. 2<sup>r</sup>       System 10–12: T. {16A–17A}. </p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    return soup


@pytest.fixture(name='sample_soup_paras')
def fixture_sample_soup_paras(sample_soup):
    """Return a list of <p> elements from the sample soup."""
    return sample_soup.find_all('p')


class TestFindSiglumIndices:
    """Tests for the find_siglum_indices function."""

    def test_with_single_siglum(self, helper):
        """Test that a single siglum is found."""
        # Arrange
        para1 = BeautifulSoup('<p><strong>A</strong></p>', 'html.parser').p
        para2 = BeautifulSoup('<p><strong>B</strong></p>', 'html.parser').p
        para3 = BeautifulSoup('<p><strong>Z</strong></p>', 'html.parser').p
        para4 = BeautifulSoup('<p><strong>D</strong> Text</p>', 'html.parser').p
        para5 = BeautifulSoup('<p>E</p>', 'html.parser').p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = [0, 1, 2]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_multiple_siglums(self, helper):
        """Test that multiple siglums are found."""
        # Arrange
        para1 = BeautifulSoup('<p><strong>C</strong></p>', 'html.parser').p
        para2 = BeautifulSoup('<p><strong>I</strong></p>', 'html.parser').p
        para3 = BeautifulSoup('<p><strong>AB</strong></p>', 'html.parser').p
        para4 = BeautifulSoup('<p><strong>E</strong>F</p>', 'html.parser').p
        para5 = BeautifulSoup(
            '<p><strong>G</strong><strong>H</strong></p>', 'html.parser').p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = [0, 1]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_siglum_in_brackets(self, helper):
        """Test that a siglum in brackets (missing) is found."""
        # Arrange
        para1 = BeautifulSoup('<p><strong>[A]</strong></p>', 'html.parser').p
        para2 = BeautifulSoup('<p><strong>[B]</strong></p>', 'html.parser').p
        para3 = BeautifulSoup('<p><strong>[Z]</strong></p>', 'html.parser').p
        para4 = BeautifulSoup('<p><strong>[D]</strong> Text</p>', 'html.parser').p
        para5 = BeautifulSoup('<p>E</p>', 'html.parser').p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = [0, 1, 2]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_optional_additional_siglum(self, helper):
        """Test that an optional (superscripted) additional siglum is found."""
        # Arrange
        para1 = BeautifulSoup('<p><strong>A<sup>a</sup></strong></p>', 'html.parser').p
        para2 = BeautifulSoup('<p><strong>B<sup>H</sup></strong></p>', 'html.parser').p
        para3 = BeautifulSoup('<p><strong>C<sup>F1</sup></strong></p>', 'html.parser').p
        para4 = BeautifulSoup('<p><strong>C<sup>F1–2</sup></strong></p>', 'html.parser').p
        para5 = BeautifulSoup('<p><strong>A<sup>aa</sup></strong></p>', 'html.parser').p
        para6 = BeautifulSoup('<p><strong>AA</strong></p>', 'html.parser').p
        para7 = BeautifulSoup('<p><strong>A</strong>a</p>', 'html.parser').p
        para8 = BeautifulSoup('<p><strong>A</strong>A', 'html.parser').p
        para9 = BeautifulSoup(
            '<p><strong>A</strong><strong>a</strong></p>', 'html.parser').p
        paras = [para1, para2, para3, para4, para5, para6, para7, para8, para9]
        expected_indices = [0, 1, 2, 3]
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_with_no_siglums(self, helper):
        """Test that no siglums are found."""
        # Arrange
        para1 = BeautifulSoup('<p>A</p>', 'html.parser').p
        para2 = BeautifulSoup('<p>BB</p>', 'html.parser').p
        para4 = BeautifulSoup('<p>C<strong></strong></p>', 'html.parser').p
        para3 = BeautifulSoup('<p><strong></strong>D</p>', 'html.parser').p
        para5 = BeautifulSoup('<p><strong></strong></p>', 'html.parser').p
        paras = [para1, para2, para3, para4, para5]
        expected_indices = []
        # Act
        actual_indices = helper.find_siglum_indices(paras)
        # Assert
        assert actual_indices == expected_indices

    def test_in_fixture_paras(self, helper, sample_soup_paras):
        """Test that the correct indices are found in the fixture sample paras."""
        # Arrange
        expected_indices = [1, 16]
        # Act
        actual_indices = helper.find_siglum_indices(sample_soup_paras)
        # Assert
        assert actual_indices == expected_indices


class TestFindTagWithLabelInSoup:
    """Tests for the _find_tag_with_label_in_soup function."""

    def test_if_label_found(self, helper):
        """Test that a label is found in the tag."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Label: Paragraph 2</p>', 'html.parser').p
        ]
        label = 'Label:'
        expected_tag_with_label = paras[1]
        # Act
        actual_tag_with_label = helper._find_tag_with_label_in_soup(label, paras)
        # Assert
        assert isinstance(actual_tag_with_label, Tag)
        assert actual_tag_with_label == expected_tag_with_label

    def test_if_label_not_found(self, helper):
        """Test that the tag is None if the label is not found."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Paragraph 2</p>', 'html.parser').p
        ]
        label = 'Label:'
        # Act
        actual_tag_with_label = helper._find_tag_with_label_in_soup(label, paras)
        # Assert
        assert actual_tag_with_label is None

    def test_if_label_is_empty(self, helper):
        """Test that the tag is None if the label is empty."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Paragraph 2</p>', 'html.parser').p
        ]
        label = ''
        expected_tag_with_label = None
        # Act
        actual_tag_with_label = helper._find_tag_with_label_in_soup(label, paras)
        # Assert
        assert actual_tag_with_label == expected_tag_with_label

    def test_if_label_is_none(self, helper):
        """Test that the tag is None if the label is None."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Paragraph 2</p>', 'html.parser').p
        ]
        label = None
        expected_tag_with_label = None
        # Act
        actual_tag_with_label = helper._find_tag_with_label_in_soup(label, paras)
        # Assert
        assert actual_tag_with_label == expected_tag_with_label

    def test_in_fixture_paras(self, helper, sample_soup_paras):
        """Test that the correct tag with label is found in the fixture sample paras."""
        # Arrange
        label = 'Beschreibstoff:'
        expected_tag_with_label = sample_soup_paras[5]
        # Act
        actual_tag_with_label = helper._find_tag_with_label_in_soup(label, sample_soup_paras)
        # Assert
        assert isinstance(actual_tag_with_label, Tag)
        assert actual_tag_with_label == expected_tag_with_label


class TestGetParagraphContentByLabel:
    """Tests for the _get_paragraph_content_by_label function."""

    def test_if_content_found(self, helper):
        """Test that the correct content of a paragraph is returned as array if found."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Label: Paragraph 2</p>', 'html.parser').p
        ]
        label = 'Label:'
        expected_content = ['Paragraph 2']
        # Act
        actual_content = helper._get_paragraph_content_by_label(label, paras)
        # Assert
        assert actual_content == expected_content

    def test_if_content_returned_without_punctuation_marks(self, helper):
        """
        Test that the correct content of a paragraph is returned as array 
        without final punctuation marks if found.
        """
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Label: Paragraph 2.</p>', 'html.parser').p
        ]
        label = 'Label:'
        expected_content = ['Paragraph 2']
        # Act
        actual_content = helper._get_paragraph_content_by_label(label, paras)
        # Assert
        assert actual_content == expected_content

    def test_if_content_found_with_multiple_lines(self, helper):
        """Test that multiple paragraphs are returned as array if found."""
        # Arrange
        html = """
            <p>Paragraph 1</p><p>Label: Paragraph 2 Part 1; </p><p>Paragraph 2 Part 2;</p><p>Paragraph 2 Part 3.</p><p>Paragraph 3</p>
            """
        soup = BeautifulSoup(html, 'html.parser')
        paras = soup.find_all('p')
        for para in paras:
            print(para)
        label = 'Label:'
        expected_content = ['Paragraph 2 Part 1', 'Paragraph 2 Part 2', 'Paragraph 2 Part 3']
        # Act
        actual_content = helper._get_paragraph_content_by_label(label, paras)
        # Assert
        assert actual_content == expected_content

    def test_if_content_not_found(self, helper):
        """Test that empty array is returned if the content is not found."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Paragraph 2</p>', 'html.parser').p
        ]
        label = 'Label:'
        expected_content = []
        # Act
        actual_content = helper._get_paragraph_content_by_label(label, paras)
        # Assert
        assert actual_content == expected_content

    def test_if_in_fixture(self, helper, sample_soup_paras):
        """Test that the correct content of a paragraph is returned if found."""
        # Arrange
        label = 'Beschreibstoff:'
        expected_content = [
            'Notenpapier, 28 Systeme, Format: hoch 343 × 264 mm, Firmenzeichen abgerissen',
            (
                'Notenpapier, 12 Systeme (unten beschnitten), Format (quer): '
                '163 × 255 mm, kein Firmenzeichen'
            )
        ]
        # Act
        actual_content = helper._get_paragraph_content_by_label(label, sample_soup_paras)
        # Assert
        assert actual_content == expected_content


class TestGetParagraphIndexByLabel:
    """Tests for the _get_paragraph_index_by_label function."""

    def test_if_label_found(self, helper):
        """Test that the correct index is returned if the label is found."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Label: Paragraph 2</p>', 'html.parser').p
        ]
        label = 'Label:'
        expected_index = 1
        # Act
        actual_index = helper._get_paragraph_index_by_label(label, paras)
        # Assert
        assert actual_index == expected_index

    def test_if_label_not_found(self, helper):
        """Test that -1 is returned if the label is not found."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Paragraph 2</p>', 'html.parser').p
        ]
        label = 'Label:'
        expected_index = -1
        # Act
        actual_index = helper._get_paragraph_index_by_label(label, paras)
        # Assert
        assert actual_index == expected_index

    def test_if_label_is_empty(self, helper):
        """Test that -1 is returned if the label is empty."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Paragraph 2</p>', 'html.parser').p
        ]
        label = ''
        expected_index = -1
        # Act
        actual_index = helper._get_paragraph_index_by_label(label, paras)
        # Assert
        assert actual_index == expected_index

    def test_if_label_is_none(self, helper):
        """Test that -1 is returned if the label is None."""
        # Arrange
        paras = [
            BeautifulSoup('<p>Paragraph 1</p>', 'html.parser').p,
            BeautifulSoup('<p>Paragraph 2</p>', 'html.parser').p
        ]
        label = None
        expected_index = -1
        # Act
        actual_index = helper._get_paragraph_index_by_label(label, paras)
        # Assert
        assert actual_index == expected_index

    def test_in_fixture_paras(self, helper, sample_soup_paras):
        """Test that the correct index is returned 
            if the label is found in the fixture sample paras."""
        # Arrange
        label = 'Inhalt:'
        expected_index = 8
        # Act
        actual_index = helper._get_paragraph_index_by_label(label, sample_soup_paras)
        # Assert
        assert actual_index == expected_index


class TestReplaceGlyphs:
    """Tests for the _replace_glyphs function."""

    def test_without_accid_glyphs(self, helper):
        """Test with glyphs that do not require the 'accid' class."""
        input_text = "[f] [ff] [fff] [mp] [ped]"
        expected_output = (
            "<span class='glyph'>{{ref.getGlyph('f')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('ff')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('fff')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('mp')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('ped')}}</span>"
        )
        assert helper._replace_glyphs(input_text) == expected_output

    def test_with_accid_glyphs(self, helper):
        """Test with glyphs that require the 'accid' class."""
        input_text = "[a] [b] [bb] [#] [x]"
        expected_output = (
            "<span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('b')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('bb')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('#')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('x')}}</span>"
        )
        assert helper._replace_glyphs(input_text) == expected_output

    def test_with_mixed_glyphs(self, helper):
        """Test with a mix of accid and non-accid glyphs."""
        input_text = "[a] [f] [bb] [mp] [#]"
        expected_output = (
            "<span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('f')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('bb')}}</span> "
            "<span class='glyph'>{{ref.getGlyph('mp')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('#')}}</span>"
        )
        assert helper._replace_glyphs(input_text) == expected_output

    def test_with_partial_matches(self, helper):
        """Test with text containing partial matches."""
        input_text = "This is a test string [a] with some glyphs [abc] [b] [bb] [#] [xylophone]"
        expected_output = (
            "This is a test string <span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "with some glyphs [abc] <span class='glyph accid'>{{ref.getGlyph('b')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('bb')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('#')}}</span> [xylophone]"
        )
        assert helper._replace_glyphs(input_text) == expected_output

    def test_replace_glyphs_with_hyphen_exclusion(self, helper):
        """Test that glyphs followed by a hyphen are not replaced."""
        input_text = "[a] [b] [bb-] [#-] [x]"
        expected_output = (
            "<span class='glyph accid'>{{ref.getGlyph('a')}}</span> "
            "<span class='glyph accid'>{{ref.getGlyph('b')}}</span> [bb-] [#-] "
            "<span class='glyph accid'>{{ref.getGlyph('x')}}</span>"
        )
        assert helper._replace_glyphs(input_text) == expected_output

    def test_with_no_glyphs(self, helper):
        """Test with text that contains no glyphs."""
        input_text = "This is a test string with no glyphs."
        expected_output = "This is a test string with no glyphs."
        assert helper._replace_glyphs(input_text) == expected_output

    def test_with_empty_string(self, helper):
        """Test that an empty string is returned as an empty string."""
        # Arrange
        input_string = ''
        expected_result = ''
        # Act
        actual_result = helper._replace_glyphs(input_string)
        # Assert
        assert actual_result == expected_result


class TestStripByDelimiter:
    """Tests for the _strip_by_delimiter function."""

    @pytest.mark.parametrize('input_string, delimiter, expected_result', [
        ('a, b, c', ',', ['a', 'b', 'c']),
        ('a; b; c', ';', ['a', 'b', 'c']),
        ('a: b: c', ':', ['a', 'b', 'c']),
        ('a| b| c', '|', ['a', 'b', 'c']),
    ])
    def test_with_single_occurence(
        self,
        helper,
        input_string,
        delimiter,
        expected_result
    ):
        """Test that the input string with single occurcence is stripped correctly."""
        # Act
        actual_stripped_result = helper._strip_by_delimiter(input_string, delimiter)
        # Assert
        assert actual_stripped_result == expected_result

    @pytest.mark.parametrize('input_string, delimiter, expected_result', [
        ('a ,b ,, c', ',', ['a', 'b', '', 'c']),
        ('a ;b ;; c', ';', ['a', 'b', '', 'c']),
        ('a :b :: c', ':', ['a', 'b', '', 'c']),
        ('a |b || c', '|', ['a', 'b', '', 'c'])
    ])
    def test_with_multiple_occurences(
        self,
        helper,
        input_string,
        delimiter,
        expected_result
    ):
        """Test that the input string with multiple occurences is stripped correctly."""
        # Act
        actual_stripped_result = helper._strip_by_delimiter(input_string, delimiter)

        # Assert
        assert actual_stripped_result == expected_result

    @pytest.mark.parametrize('input_string, delimiter, expected_result', [
        ('a, b; c', ';', ['a, b', 'c']),
        ('a, b; c', ',', ['a', 'b; c']),
        ('a, b; c', ':', ['a, b; c']),
        ('a, b; c', '|', ['a, b; c']),
    ])
    def test_with_different_delimiters(
        self,
        helper,
        input_string,
        delimiter,
        expected_result
    ):
        """Test that the input string is stripped correctly with different delimiters."""
        # Act
        actual_stripped_result = helper._strip_by_delimiter(input_string, delimiter)
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_leading_delimiter(self, helper):
        """Test that the input string with leading delimiter is stripped correctly."""
        # Arrange
        expected_result = ['', 'a', 'b', 'c']
        # Act
        actual_stripped_result = helper._strip_by_delimiter(',a, b, c', ',')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_trailing_delimiter(self, helper):
        """Test that the input string with trailing delimiter is stripped correctly."""
        # Arrange
        expected_result = ['a', 'b', 'c', '']
        # Act
        actual_stripped_result = helper._strip_by_delimiter('a, b, c,', ',')
        # Assert
        assert actual_stripped_result == expected_result

    @pytest.mark.parametrize('input_string, delimiter, expected_result', [
        ('a, b, c', ',', ['a', 'b', 'c']),
        (' a ,b, c ', ',', ['a', 'b', 'c']),
        ('   a   ,   b   ,   c   ', ',', ['a', 'b', 'c']),
    ])
    def test_with_whitespace(
        self,
        helper,
        input_string,
        delimiter,
        expected_result
    ):
        """Test that the input string with whitespace is stripped correctly."""
        # Act
        actual_stripped_result = helper._strip_by_delimiter(input_string, delimiter)
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_delimiter_not_found(self, helper):
        """Test that it returns the input string when the delimiter is not found."""
        # Arrange
        expected_result = ['abcd']
        # Act
        actual_stripped_result = helper._strip_by_delimiter('abcd', ',')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_empty_string_input(self, helper):
        """Test that it returns an empty list when the input string is empty."""
        # Arrange
        expected_result = ['']
        # Act
        actual_stripped_result = helper._strip_by_delimiter('', ',')
        # Assert
        assert actual_stripped_result == expected_result


class TestStripTagAndClean:
    """Tests for the _strip_tag_and_clean function."""

    def test_valid_tags(self, helper):
        """Test stripping valid tags and cleaning content."""
        # Arrange
        content = "<td><p>Test Content</p></td>"
        tag = "td"
        expected_result = "Test Content"
        # Act
        result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert result == expected_result

    def test_nested_tags(self, helper):
        """Test stripping nested tags and cleaning content."""
        # Arrange
        content = "<td><p><strong>Strong Nested Content</strong></p></td>"
        tag = "td"
        expected_result = "<strong>Strong Nested Content</strong>"
        # Act
        result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert result == expected_result

    def test_multiple_paragraphs(self, helper):
        """Test replacing multiple <p> tags with <br />."""
        # Arrange
        content = "<td><p>First paragraph</p><p>Second paragraph</p></td>"
        tag = "td"
        expected_result = "First paragraph <br /> Second paragraph"
        # Act
        result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert result == expected_result

    def test_multiple_paragraphs_with_nested_tags(self, helper):
        """Test replacing multiple <p> tags with <br />."""
        # Arrange
        content = "<td><p><strong>First paragraph</strong></p><p><em>Second paragraph</em></p></td>"
        tag = "td"
        expected_result = "<strong>First paragraph</strong> <br /> <em>Second paragraph</em>"
        # Act
        result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert result == expected_result

    def test_malformed_tags(self, helper):
        """Test content with malformed tags."""
        # Arrange
        content = "<td><p><strong>Malformed Content</p></td>"
        tag = "td"
        expected_result = "<strong>Malformed Content"
        # Act
        result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert result == expected_result

    def test_no_matching_tags(self, helper):
        """Test content with no matching tags."""
        # Arrange
        content = "<p>No matching tags here</p>"
        tag = "td"
        expected_result = ""
        # Act
        result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert result == expected_result

    def test_empty_content(self, helper):
        """Test empty content."""
        # Arrange
        content = ""
        tag = "td"
        expected_result = ""
        # Act
        result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert result == expected_result

    def test_with_none(self, helper):
        """Test that it returns an empty string when passed None."""
        # Arrange
        content = None
        tag = "strong"
        expected_result = ''
        # Act
        actual_stripped_result = helper._strip_tag_and_clean(content, tag)
        # Assert
        assert actual_stripped_result == expected_result


class TestStripTag:
    """Tests for the _strip_tag function."""

    def test_with_p(self, helper):
        """Test that it strips a paragraph tag."""
        # Arrange
        content = '<p>Hello, World!</p>'
        expected_result = 'Hello, World!'
        # Act
        actual_stripped_result = helper._strip_tag(content, 'p')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_div(self, helper):
        """Test that it strips a div tag."""
        # Arrange
        content = '<div> This is a div </div>'
        expected_result = 'This is a div'
        # Act
        actual_stripped_result = helper._strip_tag(content, 'div')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_h1(self, helper):
        """Test that it strips a heading tag."""
        # Arrange
        content = '<h1> Heading 1 </h1>'
        expected_result = 'Heading 1'
        # Act
        actual_stripped_result = helper._strip_tag(content, 'h1')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_nested_tag(self, helper):
        """Test that it strips a nested tag."""
        # Arrange
        content = '<p><strong>This is a nested tag</strong></p>'
        expected_result = '<strong>This is a nested tag</strong>'
        # Act
        actual_stripped_result = helper._strip_tag(content, 'p')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_empty_tag(self, helper):
        """Test that it returns an empty tag when passed an empty tag."""
        # Arrange
        content = '<p></p>'
        expected_result = ''
        # Act
        actual_stripped_result = helper._strip_tag(content, 'p')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_plain_text(self, helper):
        """Test that it returns the plain text when passed plain text."""
        # Arrange
        content = 'This is a plain text'
        expected_result = 'This is a plain text'
        # Act
        actual_stripped_result = helper._strip_tag(content, 'p')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_empty_string(self, helper):
        """Test that it returns an empty string when passed an empty string."""
        # Arrange
        content = ''
        expected_result = ''
        # Act
        actual_stripped_result = helper._strip_tag(content, 'p')
        # Assert
        assert actual_stripped_result == expected_result

    def test_with_none(self, helper):
        """Test that it returns an empty string when passed None."""
        # Arrange
        content = None
        expected_result = ''
        # Act
        actual_stripped_result = helper._strip_tag(content, 'p')
        # Assert
        assert actual_stripped_result == expected_result
