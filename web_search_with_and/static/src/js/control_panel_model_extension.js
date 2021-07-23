odoo.define("web_search_with_and/static/src/js/control_panel_model_extension.js", function (require) {
    "use strict";

    const ControlPanelModelExtension = require("web/static/src/js/control_panel/control_panel_model_extension.js");
    
    ControlPanelModelExtension.prototype.addAutoCompletionValues = function({ filterId, label, value, operator, withShift }){
        const queryElem = this.state.query.find(queryElem =>
            queryElem.filterId === filterId &&
            queryElem.value === value &&
            queryElem.operator === operator
        );
        if (!queryElem) {
            var { groupId } = this.state.filters[filterId];
            if(withShift){
                groupId = this.state.query.length + 1000;  
            }
            this.state.query.push({ filterId, groupId, label, value, operator });
        } else {
            queryElem.label = label;
        }
    },

    ControlPanelModelExtension.prototype._activateDefaultFilters = function(){
        if (this.defaultFavoriteId) {
            // Activate default favorite
            this.toggleFilter(this.defaultFavoriteId);
        } else {
            // Activate default filters
            Object.values(this.state.filters)
                .filter((f) => f.isDefault && f.type !== 'favorite')
                .sort((f1, f2) => (f1.defaultRank || 100) - (f2.defaultRank || 100))
                .forEach(f => {
                    if (f.hasOptions) {
                        this.toggleFilterWithOptions(f.id);
                    } else if (f.type === 'field') {
                        let { operator, label, value } = f.defaultAutocompleteValue;
                        this.addAutoCompletionValues({
                            filterId: f.id,
                            value,
                            operator,
                            label,
                            withShift : false,
                        });
                    } else {
                        this.toggleFilter(f.id);
                    }
                });
        }
    }

});
