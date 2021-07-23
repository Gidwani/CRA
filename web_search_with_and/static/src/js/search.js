odoo.define("web_search_with_and", function(require) {
    "use strict";

    var SearchBar = require("web.SearchBar");

    SearchBar.prototype._selectSource = function(source){
        if (source.active) {
            const labelValue = source.label || this.state.inputValue;
            this.model.dispatch('addAutoCompletionValues', {
                filterId: source.filterId,
                value: "value" in source ? source.value : this._parseWithSource(labelValue, source),
                label: labelValue,
                operator: source.filterOperator || source.operator,
                withShift: source.shiftKey,
            });
        }
        this._closeAutoComplete();
    },
    SearchBar.prototype._onSearchKeydown = function(ev){
        if (ev.isComposing) {
            // This case happens with an IME for example: we let it handle all key events.
            return;
        }
        const currentItem = this.state.sources[this.state.focusedItem] || {};
        switch (ev.key) {
            case 'ArrowDown':
                ev.preventDefault();
                if (Object.keys(this.state.sources).length) {
                    let nextIndex = this.state.focusedItem + 1;
                    if (nextIndex >= this.state.sources.length) {
                        nextIndex = 0;
                    }
                    this.state.focusedItem = nextIndex;
                } else {
                    this.env.bus.trigger('focus-view');
                }
                break;
            case 'ArrowLeft':
                if (currentItem.expanded) {
                    // Priority 1: fold expanded item.
                    ev.preventDefault();
                    this._expandSource(currentItem, false);
                } else if (currentItem.parent) {
                    // Priority 2: focus parent item.
                    ev.preventDefault();
                    this.state.focusedItem = this.state.sources.indexOf(currentItem.parent);
                    // Priority 3: Do nothing (navigation inside text).
                } else if (ev.target.selectionStart === 0) {
                    // Priority 4: navigate to rightmost facet.
                    this._focusFacet(this.model.get("facets").length - 1);
                }
                break;
            case 'ArrowRight':
                if (ev.target.selectionStart === this.state.inputValue.length) {
                    // Priority 1: Do nothing (navigation inside text).
                    if (currentItem.expand) {
                        // Priority 2: go to first child or expand item.
                        ev.preventDefault();
                        if (currentItem.expanded) {
                            this.state.focusedItem ++;
                        } else {
                            this._expandSource(currentItem, true);
                        }
                    } else if (ev.target.selectionStart === this.state.inputValue.length) {
                        // Priority 3: navigate to leftmost facet.
                        this._focusFacet(0);
                    }
                }
                break;
            case 'ArrowUp':
                ev.preventDefault();
                let previousIndex = this.state.focusedItem - 1;
                if (previousIndex < 0) {
                    previousIndex = this.state.sources.length - 1;
                }
                this.state.focusedItem = previousIndex;
                break;
            case 'Backspace':
                if (!this.state.inputValue.length) {
                    const facets = this.model.get("facets");
                    if (facets.length) {
                        this._onFacetRemove(facets[facets.length - 1]);
                    }
                }
                break;
            case 'Enter':
                if (!this.state.inputValue.length) {
                    this.model.dispatch('search');
                    break;
                }
                /* falls through */
            case 'Tab':
                if (this.state.inputValue.length) {
                    ev.preventDefault(); // keep the focus inside the search bar
                    if(ev.shiftKey){
                        currentItem.shiftKey = true;
                    }else{
                        currentItem.shiftKey = false;
                    }
                    this._selectSource(currentItem);
                }
                break;
            case 'Escape':
                if (this.state.sources.length) {
                    this._closeAutoComplete();
                }
                break;
        }
    }
});
