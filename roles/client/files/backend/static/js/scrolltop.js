/*
 *
 * Copyright IBM Corp, 2016
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
 * implied. See the License for the specific language governing
 * permissions and limitations under the License.
 *
 */

// Handles the back to top button

$(document).ready(function() {
    var scroll_offset = 200;
    var btnBck2Top = $('#btn-bck2top');

    if($(window).scrollTop() > scroll_offset) {
        $(btnBck2Top).show();
    }

    $(window).scroll(function() {
        if($(this).scrollTop() > scroll_offset) {
            $(btnBck2Top).show();
        } else {
            $(btnBck2Top).hide();
        }
    });

    $(btnBck2Top).click(function(event) {
        event.preventDefault();
        $('body,html').animate({scrollTop: 0});
    });
});

