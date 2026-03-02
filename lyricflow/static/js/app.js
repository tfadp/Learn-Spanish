/**
 * LyricFlow — Alpine.js Shared Components
 *
 * Page-specific components are defined inline in their templates
 * (library.html, song.html, add_song.html).
 *
 * This file holds only shared utilities loaded on every page.
 * Follows SPECS.md data shapes and domain rules.
 */


// ---------------------------------------------------------------------------
// app() — Song Library component (legacy, kept for compatibility)
// ---------------------------------------------------------------------------
function app() {
    return {
        songs: [],
        filter: 'all',
        loading: true,

        async init() {
            try {
                const res = await fetch('/api/songs');
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                this.songs = await res.json();
            } catch (err) {
                console.error('Failed to load songs:', err);
                this.songs = [];
            } finally {
                this.loading = false;
            }
        },

        get filteredSongs() {
            if (this.filter === 'all') return this.songs;
            return this.songs.filter(s => s.language === this.filter);
        },

        progressPercent(song) {
            const raw = song.mastery_progress ?? 0;
            return Math.round(raw * 100);
        },
    };
}
