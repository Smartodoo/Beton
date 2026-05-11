/* @odoo-module */

import { Component, useState, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class CalculaterSh extends Component {
       static template = "CalculatorTemplate";

       setup() {
            this.orm = useService("orm");
            this.onWillStart()
        }

       async onWillStart() {
            const data = await this.orm.searchRead(
            "res.users",
            [['id', '=', session.uid]],
            ["sh_enable_calculator_mode"]
            );

            if (data) {
                if (! data[0].sh_enable_calculator_mode) {
                    $('.sh_calc_util').hide();
                    }
            }
       }


       onClickCalculator() {
          if($('.calculator').length > 0){
        	  $(".sh_calc_results").html("");
          }else{
              // render template
              var qweb_data = '<script type="text/javascript" src="/sh_entmate_theme/static/src/js/calculate.js"></script>
                                <div class="calculator" align="center">
                                 <div class="row displayBox">
                                   <p class="displayText" id="display">0</p>
                                 </div>
                                        <div class="row numberPad">
                                   <div class="col-md-12">
                                     <div class="row">
                                       <button class="btn clear hvr-back-pulse" id="clear">C</button>
                                         <button class="btn btn-calc hvr-radial-out" id="sqrt">√</button>
                                         <button class="btn btn-calc hvr-radial-out hvr-radial-out" id="square">x<sup>2</sup></button>
                                         <button id="divide" class="btn btn-operation hvr-fade">÷</button>
                                     </div>
                                       <div class="row">
                                       <button class="btn btn-calc hvr-radial-out" id="seven">7</button>
                                           <button class="btn btn-calc hvr-radial-out" id="eight">8</button>
                                           <button class="btn btn-calc hvr-radial-out" id="nine">9</button>
                                           <button id="multiply" class="btn btn-operation hvr-fade">×</button>
                                     </div>
                                       <div class="row">
                                       <button class="btn btn-calc hvr-radial-out" id="four">4</button>
                                           <button class="btn btn-calc hvr-radial-out" id="five">5</button>
                                           <button class="btn btn-calc hvr-radial-out" id="six">6</button>
                                           <button id="subtract" class="btn btn-operation hvr-fade">−</button>
                                     </div>
                                       <div class="row">
                                       <button class="btn btn-calc hvr-radial-out" id="one">1</button>
                                           <button class="btn btn-calc hvr-radial-out" id="two">2</button>
                                           <button class="btn btn-calc hvr-radial-out" id="three">3</button>
                                           <button id="add" class="btn btn-operation hvr-fade">+</button>
                                     </div>
                                       <div class="row">
                                       <button class="btn btn-calc hvr-radial-out" id="plus_minus">&#177;</button>
                                           <button class="btn btn-calc hvr-radial-out" id="zero">0</button>
                                           <button class="btn btn-calc hvr-radial-out" id="decimal">.</button>
                                           <button id="equals" class="btn btn-operation equals hvr-back-pulse">=</button>
                                     </div>
                                   </div>
                                 </div>
                               </div>'
        	  $(".sh_calc_results").html(qweb_data);
          }

          if($('.sh_calc_util').hasClass('active')){
        	  $('.sh_calc_util').removeClass('active')
          }else{
        	  $('.sh_calc_util').addClass('active')
          }

          // close other popup
          $('.sh_user_language_list_cls').css("display","none")
          $('.sh_wqm_quick_menu_submenu_list_cls').css("display","none")
          $('.todo_layout').removeClass("sh_theme_model");
       }

}

registry.category("systray").add("sh_entmate_theme.calculater_sh", { Component: CalculaterSh }, { sequence: 25 });