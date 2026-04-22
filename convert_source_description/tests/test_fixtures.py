"""Shared pytest fixtures for convert_source_description tests."""

import pytest
from bs4 import BeautifulSoup


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
            <p>Skizzen zu &lt;br /&gt;&lt;span class="tab"&gt;&lt;/span&gt;Studienkomposition für Klavier / Streichquartett M 22.&lt;br /&gt;Enthält auch Skizzen zu Studienkomposition für Klavier M* 411–412 sowie Tintenniederschrift von Studienkomposition für Streichquartett M* 408. </p>
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
    return BeautifulSoup(html, "html.parser")


@pytest.fixture(name="sample_soup_paras")
def fixture_sample_soup_paras(sample_soup):
    """Return a list of <p> elements from the sample soup."""
    return sample_soup.find_all("p")
