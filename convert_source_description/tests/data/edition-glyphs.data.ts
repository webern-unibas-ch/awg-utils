/**
 * Object constant: EDITION_GLYPHS_DATA.
 *
 * Trimmed test copy of awg-app/src/app/views/edition-view/data/edition-glyphs.data.ts
 * (all sections, but only some of the dynamics).
 */
export const EDITION_GLYPHS_DATA = {
    /** ***********************************/
    /**            ACCIDENTALS             /
    /** ***********************************/
    /**
     * The glyph of a music double flat sign.
     * Cf. https://w3c.github.io/smufl/latest/tables/standard-accidentals-12-edo.html
     */
    DOUBLE_FLAT: {
        alt: '[bb]',
        hex: '',
    },

    /**
     * The glyph of a music double sharp sign.
     * Cf. https://w3c.github.io/smufl/latest/tables/standard-accidentals-12-edo.html
     */
    DOUBLE_SHARP: {
        alt: '[x]',
        hex: '',
    },

    /**
     * The glyph of a music flat sign.
     * Cf. https://w3c.github.io/smufl/latest/tables/standard-accidentals-12-edo.html
     */
    FLAT: {
        alt: '[b]',
        hex: '',
    },

    /**
     * The glyph of a music natural sign.
     * Cf. https://w3c.github.io/smufl/latest/tables/standard-accidentals-12-edo.html
     */
    NATURAL: {
        alt: '[a]',
        hex: '',
    },

    /**
     * The glyph of a music sharp sign.
     * Cf. https://w3c.github.io/smufl/latest/tables/standard-accidentals-12-edo.html
     */
    SHARP: {
        alt: '[#]',
        hex: '',
    },

    /** ***********************************/
    /**         ARTICULATIONS              /
    /** ***********************************/
    /**
     * The glyph of a musical accent above symbol.
     * Cf. https://w3c-cg.github.io/smufl/latest/tables/articulation.html
     */
    ACCENT_ABOVE: {
        alt: '[>]',
        hex: '',
    },

    /** ********************************/
    /**            DYNAMICS             /
    /** ********************************/
    /**
     * The glyph of a musical forte symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/dynamics.html
     */
    FORTE: {
        alt: '[f]',
        hex: '',
    },

    /**
     * The glyph of a musical fortissimo (double forte) symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/dynamics.html
     */
    FORTISSIMO: {
        alt: '[ff]',
        hex: '',
    },

    /**
     * The glyph of a musical triple forte symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/dynamics.html
     */
    FORTISSIMO3: {
        alt: '[fff]',
        hex: '',
    },

    /**
     * The glyph of a musical mezzo piano symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/dynamics.html
     */
    MEZZOPIANO: {
        alt: '[mp]',
        hex: '',
    },

    /** ***********************************/
    /**            NOTE VALUES             /
    /** ***********************************/
    /**
     * The glyph of a musical eighth note symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/individual-notes.html
     */
    NOTE_EIGHTH: {
        alt: '[Achtelnote]',
        hex: '',
    },

    /**
     * The glyph of a musical half note symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/individual-notes.html
     */
    NOTE_HALF: {
        alt: '[Halbe Note]',
        hex: '',
    },

    /**
     * The glyph of a musical half note with dot symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/individual-notes.html
     */
    NOTE_HALF_DOTTED: {
        alt: '[Punktierte Halbe Note]',
        hex: ' ',
    },

    /**
     * The glyph of a musical quarter note symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/individual-notes.html
     */
    NOTE_QUARTER: {
        alt: '[Viertelnote]',
        hex: '',
    },

    /**
     * The glyph of a musical sixteenth note symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/individual-notes.html
     */
    NOTE_SIXTEENTH: {
        alt: '[Sechzehntelnote]',
        hex: '',
    },

    /**
     * The glyph of a musical whole note symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/individual-notes.html
     */
    NOTE_WHOLE: {
        alt: '[Ganze Note]',
        hex: '',
    },

    /** ***********************************/
    /**         PLAYING TECHNIQUES         /
    /** ***********************************/
    /**
     * The glyph of a musical pedal symbol.
     * Cf. https://w3c.github.io/smufl/latest/tables/keyboard-techniques.html
     */
    PEDAL: {
        alt: '[ped]',
        hex: '',
    },
} as const;
