/** @odoo-module **/

const { Component, hooks } = owl;
const rpc = require("web.rpc");
const session = require("web.session");
import { onMounted, useExternalListener, useState } from "@odoo/owl";
const { useListener } = require("@web/core/utils/hooks");
var show_zoom = false

rpc.query({
    model: 'res.users',
    method: 'search_read',
    fields: ['sh_enable_zoom'],
    domain: [['id', '=', session.uid]]
}, { async: false }).then(function (data) {
    if (data) {
        _.each(data, function (user) {
            if (user.sh_enable_zoom) {
               
                show_zoom = true
            }
        });

    }
});

export class ZoomWidget extends Component {
    setup() {
        super.setup();
        this.show_zoom = show_zoom;
    }
    setResetZoom(){
        var zoom = $('.sh_full').text().split('%')
        if($('.o_content').find('div')[0]){
            $($('.o_content').find('div')[0]).removeClass("sh_zoom_"+zoom[0])
            zoom = 100
            $('.sh_full').text(zoom.toString()+'%');
            $($('.o_content').find('div')[0]).addClass("sh_zoom_"+zoom)
        }
    }
    zoomDropdown(ev){
            if ($('.sh-zoom-panel').css('display') == 'none')
            {                   
                $('.sh-zoom-panel').css('display','table')
            }else{
                $('.sh-zoom-panel').css('display','none')
            }
       
    }
    setDecZoom(){
        var zoom = $('.sh_full').text().split('%')
        if(parseInt(zoom[0])-10 >= 20 && parseInt(zoom[0])-10 <= 200){
            if($('.o_content').find('div')[0]){
                $($('.o_content').find('div')[0]).removeClass("sh_zoom_"+zoom[0])
                zoom = parseInt(zoom[0])-10
                $('.sh_full').text(zoom.toString()+'%');
                $($('.o_content').find('div')[0]).addClass("sh_zoom_"+zoom)
            }
            
        }
        
    }
    setIncZoom(){
        var zoom = $('.sh_full').text().split('%')
        if(parseInt(zoom[0])+10 >= 20 && parseInt(zoom[0])+10 <= 200){
            if($('.o_content').find('div')[0]){
                $($('.o_content').find('div')[0]).removeClass("sh_zoom_"+zoom[0])
                zoom = parseInt(zoom[0])+10
                $('.sh_full').text(zoom.toString()+'%');
                $($('.o_content').find('div')[0]).addClass("sh_zoom_"+zoom)
            }
        }
       
    }

}
    

ZoomWidget.template = 'ZoomWidget';
// NavFooter.components = { NotUpdatable, ErrorHandler };
