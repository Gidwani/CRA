odoo.define('odoo_advance_search.ListController', function (require) {
"use strict";

var odoo_advance_search_utils = require('odoo_advance_search.utils');
var datepicker = require('web.datepicker');

    setInterval(function () {
        var filter_field = document.getElementsByClassName("many2one_input");
        var from_date = $(document.getElementsByClassName("from_date_search"));
        var to_date = $(document.getElementsByClassName("to_date_search"));
        if (filter_field.length !== 0){
            for (let input = 0; input < filter_field.length; input++) {
                if ($(filter_field[input]).attr("class").match("not_many2one") === null){
                    odoo_advance_search_utils.setAsRecordSelect($(filter_field[input]));
                    $(filter_field[input]).addClass('not_many2one');
                }
            }
        }
        if (from_date.length !== 0){
            var options = { // Set the options for the datetimepickers
                locale : moment.locale(),
                format : 'M/D/YYYY',
                icons: {
                    date: "fa fa-calendar",
                },
            };
            from_date.each(function () {
                var name = $(this).attr('name');
                var defaultValue = window.advance_search[name + 'from'];
                $(this).datetimepicker(options);
                var dt = new datepicker.DateWidget(options);
                dt.replace($(this)).then(function () {
                    dt.$el.find('input').attr('name', name);
                    dt.$el.addClass("number_search")
                    dt.$el.find('input').attr('placeholder', "From:");
                    dt.$el.find('input').addClass('number_search from_date');
                    dt.$el.find('input').attr('t-on-change', '_onChangeSelection');
                    if (defaultValue) { // Set its default value if there is one
                        dt.setValue(moment(defaultValue));
                    }
                });
            });
            to_date.each(function () {
                var name = $(this).attr('name');
                var defaultValue = window.advance_search[name + 'to'];
                $(this).datetimepicker(options);
                var dt = new datepicker.DateWidget(options);
                dt.replace($(this)).then(function () {
                    dt.$el.find('input').attr('name', name);
                    dt.$el.addClass("number_search")
                    dt.$el.find('input').attr('placeholder', "To:");
                    dt.$el.find('input').addClass('number_search to_date');
                    dt.$el.find('input').attr('t-on-focusout', '_onChangeSelection');
                    if (defaultValue) { // Set its default value if there is one
                        dt.setValue(moment(defaultValue));
                    }
                });
            });
        }
    }, 500);
});
