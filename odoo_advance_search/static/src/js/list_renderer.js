/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { Record, RelationalModel } from "@web/views/relational_model";
import { registry } from "@web/core/registry";
import { Domain } from "@web/core/domain";
import { ListController } from '@web/views/list/list_controller';

export const DynamicRecordListSearch = {

    async _loadRecords() {
        var domain = this.domain
        if (this.model.env.searchModel && this.model.env.searchModel.groupBy.length === 0){
            var domain = this.model.env.searchModel._getDomain()
        }
        var filter_field = document.getElementsByClassName('number_search')
        var advance_domain = [];
        var advance_search = {};
        for (let input = 0; input < filter_field.length; input++) {
            if (filter_field[input].value !== '' && self.location && self.location.hash.match("model="+ this.resModel) !== null) {
                if ($(filter_field[input]).attr('field_type') === 'boolean') {
                    if (filter_field[input].value === 'true') {
                        advance_domain.push([filter_field[input].name, '=', true]);
                        advance_search[[filter_field[input].name]] = filter_field[input].value
                    }
                    if (filter_field[input].value === 'false') {
                        advance_domain.push([filter_field[input].name, '=', false]);
                        advance_search[[filter_field[input].name]] = filter_field[input].value
                    }
                    if (filter_field[input].value === 'no_select') {
                        advance_domain.push([filter_field[input].name, 'in', [false, true]]);
                        advance_search[[filter_field[input].name]] = filter_field[input].value
                    }
                    continue;
                }
                if (filter_field[input].type === 'select-one') {
                    if (filter_field[input].value === 'no_select') {
                        advance_domain.push([filter_field[input].name, '!=', false]);
                        advance_search[[filter_field[input].name]] = filter_field[input].value
                        continue;
                    }
                    advance_domain.push([filter_field[input].name, '=', filter_field[input].value]);
                    advance_search[[filter_field[input].name]] = filter_field[input].value
                }
                if ($(filter_field[input]).attr('field_type') === 'many2one') {
                    var values = $(filter_field[input]).data('new_id_vals') || {};
                    advance_search[[filter_field[input].name]] = values
                    values = Object.keys(values).map(Number)
                    if (values.length){
                        advance_domain.push([filter_field[input].name,'in',values]);
                    }
                    continue;
                }
                if (filter_field[input].className.match('from_date')) {
                    var new_date = new Date(new Date(filter_field[input].value.split('/').join('-')).getTime() - (1 *86400000))
                    var date = new_date.getFullYear() + '-' + (new_date.getMonth() + 1) + '-' + new_date.getDate() + ' ' + '18:30:00'
                    advance_search[[filter_field[input].name + 'from']] = filter_field[input].value
                    advance_domain.push([filter_field[input].name, '>=', date]);
                    continue;
                }
                if (filter_field[input].className.match('to_date')) {
                    var new_date = new Date(filter_field[input].value.split('/').join('-'))
                    var date = new_date.getFullYear() + '-' + (new_date.getMonth() + 1) + '-' + new_date.getDate() + ' ' + '18:29:59'
                    advance_search[[filter_field[input].name + 'to']] = filter_field[input].value
                    advance_domain.push([filter_field[input].name, '<=', date]);
                    continue;
                }
                if (filter_field[input].type === 'text') {
                    advance_search[[filter_field[input].name]] = filter_field[input].value
                    advance_domain.push([filter_field[input].name, 'ilike', filter_field[input].value]);
                }
                if (filter_field[input].type === 'number' && filter_field[input].className.match('from_int')) {
                    advance_search[[filter_field[input].name + '_from']] = filter_field[input].value
                    advance_domain.push([filter_field[input].name, '>=', parseInt(filter_field[input].value)]);
                }
                if (filter_field[input].type === 'number' && filter_field[input].className.match('to_int')) {
                    advance_search[[filter_field[input].name + '_to']] = filter_field[input].value
                    advance_domain.push([filter_field[input].name, '<=', parseInt(filter_field[input].value)]);
                }
            }
        }
        if ((this.model.env.searchModel.groupBy.length === 0) && (event && (!event.currentTarget.className || event.currentTarget.className &&
            event.currentTarget.className.match("o_back_button") === null))) {
            window.advance_search = {}
        }
        if (advance_domain.length === 0){
            if (event && (event && !event.currentTarget.className || event.currentTarget.className && event.currentTarget.className.match("number_search") === null)){
                if (event.currentTarget.className && (event.currentTarget.className.match("datetimepicker") === null ||
                    event.currentTarget.className.match('select2-search-choice-close') === null)){
                }
                else {
                    advance_domain = []
                    advance_search = []
                }
            }
        }
        if (advance_domain.length !== 0){
            window.domain = Domain.and([domain, advance_domain]).toList();
            this.domain = window.domain
            window.advance_search = advance_search
        }
        if (!_.isEmpty(window.advance_search)) {
            this.domain = window.domain
        }
        if (!window.advance_search){
            window.advance_search = {}
        }
        return this._super()
    }

//    async load() {
//        var domain = this.domain
//        if (this.model.env.searchModel && this.model.env.searchModel.groupBy.length === 0){
//            var domain = this.model.env.searchModel._getDomain()
//        }
//        var filter_field = document.getElementsByClassName('number_search')
//        var advance_domain = [];
//        var advance_search = {};
//        for (let input = 0; input < filter_field.length; input++) {
//            if (filter_field[input].value !== '' && self.location && self.location.hash.match("model="+ this.resModel) !== null) {
//                if ($(filter_field[input]).attr('field_type') === 'boolean') {
//                    if (filter_field[input].value === 'true') {
//                        advance_domain.push([filter_field[input].name, '=', true]);
//                        advance_search[[filter_field[input].name]] = filter_field[input].value
//                    }
//                    if (filter_field[input].value === 'false') {
//                        advance_domain.push([filter_field[input].name, '=', false]);
//                        advance_search[[filter_field[input].name]] = filter_field[input].value
//                    }
//                    if (filter_field[input].value === 'no_select') {
//                        advance_domain.push([filter_field[input].name, 'in', [false, true]]);
//                        advance_search[[filter_field[input].name]] = filter_field[input].value
//                    }
//                    continue;
//                }
//                if (filter_field[input].type === 'select-one') {
//                    if (filter_field[input].value === 'no_select') {
//                        advance_domain.push([filter_field[input].name, '!=', false]);
//                        advance_search[[filter_field[input].name]] = filter_field[input].value
//                        continue;
//                    }
//                    advance_domain.push([filter_field[input].name, '=', filter_field[input].value]);
//                    advance_search[[filter_field[input].name]] = filter_field[input].value
//                }
//                if ($(filter_field[input]).attr('field_type') === 'many2one') {
//                    var values = $(filter_field[input]).data('new_id_vals') || {};
//                    advance_search[[filter_field[input].name]] = values
//                    values = Object.keys(values).map(Number)
//                    if (values.length){
//                        advance_domain.push([filter_field[input].name,'in',values]);
//                    }
//                    continue;
//                }
//                if (filter_field[input].className.match('from_date')) {
//                    var new_date = new Date(new Date(filter_field[input].value.split('/').join('-')).getTime() - (1 *86400000))
//                    var date = new_date.getFullYear() + '-' + (new_date.getMonth() + 1) + '-' + new_date.getDate() + ' ' + '18:30:00'
//                    advance_search[[filter_field[input].name + 'from']] = filter_field[input].value
//                    advance_domain.push([filter_field[input].name, '>=', date]);
//                    continue;
//                }
//                if (filter_field[input].className.match('to_date')) {
//                    var new_date = new Date(filter_field[input].value.split('/').join('-'))
//                    var date = new_date.getFullYear() + '-' + (new_date.getMonth() + 1) + '-' + new_date.getDate() + ' ' + '18:29:59'
//                    advance_search[[filter_field[input].name + 'to']] = filter_field[input].value
//                    advance_domain.push([filter_field[input].name, '<=', date]);
//                    continue;
//                }
//                if (filter_field[input].type === 'text') {
//                    advance_search[[filter_field[input].name]] = filter_field[input].value
//                    advance_domain.push([filter_field[input].name, 'ilike', filter_field[input].value]);
//                }
//                if (filter_field[input].type === 'number' && filter_field[input].className.match('from_int')) {
//                    advance_search[[filter_field[input].name + '_from']] = filter_field[input].value
//                    advance_domain.push([filter_field[input].name, '>=', parseInt(filter_field[input].value)]);
//                }
//                if (filter_field[input].type === 'number' && filter_field[input].className.match('to_int')) {
//                    advance_search[[filter_field[input].name + '_to']] = filter_field[input].value
//                    advance_domain.push([filter_field[input].name, '<=', parseInt(filter_field[input].value)]);
//                }
//            }
//        }
//        if ((this.model.env.searchModel.groupBy.length === 0) && (event && (!event.currentTarget.className || event.currentTarget.className &&
//            event.currentTarget.className.match("o_back_button") === null))) {
//            window.advance_search = {}
//        }
//        if (advance_domain.length === 0){
//            if (event && (event && !event.currentTarget.className || event.currentTarget.className && event.currentTarget.className.match("number_search") === null)){
//                if (event.currentTarget.className && (event.currentTarget.className.match("datetimepicker") === null ||
//                    event.currentTarget.className.match('select2-search-choice-close') === null)){
//                }
//                else {
//                    advance_domain = []
//                    advance_search = []
//                }
//            }
//        }
//        if (advance_domain.length !== 0){
//            window.domain = Domain.and([domain, advance_domain]).toList();
//            this.domain = window.domain
//            window.advance_search = advance_search
//        }
//        if (!_.isEmpty(window.advance_search)) {
//            this.domain = window.domain
//        }
////        var data = this._super()
//        return this._super()
//    },
};
export const SearchListRenderer = {

    _onChangeSelection (e) {
        this.__owl__.props.list.model.env.searchModel._notify()
    },

    _onClickEnter (e) {
       if (e.key == 'Enter') {
            this.props.list.search = true;
            this.__owl__.props.list.model.env.searchModel._notify()
        }
    },

//    _onClickMany () {
//        odoo_advance_search_utils.setAsRecordSelect($(event.target));
//    },
};
export const ListControllerButton = {
    onClickRefreshSearch (){
        var input_search = document.getElementsByClassName("number_search")
        for (let input = 0; input < input_search.length; input++) {
            input_search[input].value = ''
        }
        $(document.getElementsByClassName("select2-search-choice-close")).click();
        if (this.model.env && this.model.env.searchModel){
            this.model.env.searchModel._notify()
        }
    }
}

patch(
    ListRenderer.prototype,
    "web_listview_range_select.WebListviewSearchListRenderer",
    SearchListRenderer
);
patch(
    RelationalModel.DynamicRecordList.prototype,
    "web_listview_range_select.WebListviewSearch",
    DynamicRecordListSearch
);
patch(
    ListController.prototype,
    "web_listview_range_select.WebListviewSearchButton",
    ListControllerButton
);
