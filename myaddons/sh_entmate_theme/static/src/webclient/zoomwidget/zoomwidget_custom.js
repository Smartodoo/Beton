/** @odoo-module **/

import { Component } from "@odoo/owl";
import { session } from "@web/session";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService, useBus } from "@web/core/utils/hooks";

/*rpc.query({
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
});*/

export class ZoomWidget extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.show_zoom = session.sh_enable_zoom
        //this.search_sh_enable_zoom()
    }

    /*search_sh_enable_zoom(){
          var self = this;
          jsonrpc("/web/dataset/call_kw/res.users/search_read", {
                    model: 'res.users',
                    method: 'search_read',
                    args: [[['id', '=', session.uid]]],
                    kwargs: {},
                }).then(function (data) {
                    
                    self.show_zoom = data[0].sh_enable_zoom
                    });
    }*/

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
