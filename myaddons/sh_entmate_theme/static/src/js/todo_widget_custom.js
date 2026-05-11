/** @odoo-module **/
import { Component, useState, xml } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from "@web/session";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { renderToElement } from "@web/core/utils/render";

var todo_card_html = ''

export class ToDoWidget extends Component {
		static template = 'ToDoWidget';
		/*events: {
            'click .close_todo_setting' : '_close_todo',
			'click .sh_add_todo': '_click_add_todo',
			'change .sh_todo_checklist':'_click_sh_todo_checklist',
			'click .sh_header_pencil':'_click_sh_header_pencil',
			'click .sh_header_save':'_focusout_sh_todo_description',
			'click .sh_header_times':'_remove_todo',
			'keydown .sh_add_todo_input': '_onKeydown',
		},*/

        setup() {
        	super.setup()
            this.orm = useService("orm");
			this.onWillStart()
		}

		 async onWillStart() {
		    var accordion_html = ''
		       var self = this
		       $("#accordion").html('')
			   await self.getAllTodo().then(function (each_data) {
					    $.each(each_data, function (todo_data) {
					    const accordion_html = renderToElement(
                            'sh_entmate_theme.todo_card', {
                            name: each_data[todo_data].name,
                            rec: each_data[todo_data].id,
                            is_done: each_data[todo_data].is_done,
                            _remove_todo: function (ev){
                                self._remove_todo(each_data[todo_data].id)
                                ev.target.parentElement.parentElement.parentElement.remove();
                            },
                            _click_sh_header_pencil : function (ev){
                                self._click_sh_header_pencil(ev)
                            },
                            _focusout_sh_todo_description : function (ev){
                                self._focusout_sh_todo_description(ev)
                            },
                            _click_sh_todo_checklist : function(ev){
                                self._click_sh_todo_checklist(ev)
                            },
                        });
                        $("#accordion").append(accordion_html);

                        // todo
                        /*$('#accordion').sortable({
						stop: function(event, ui) {
							var itemOrder = $('#accordion').sortable("toArray");
							for (var i = 0; i < itemOrder.length; i++) {
							  rpc.query({
									model: 'sh.todo',
									method: 'write',
									args: [[ itemOrder[i]], {
										sequence: i+10,
									}],
								});
							}
						  }
					    });*/

                        todo_card_html += accordion_html
					});
				});
	    }

		_onKeydown() {
			ev.stopPropagation();
			if (ev.which === 13) {
				var self = this;
				var todo_input = $(".sh_add_todo_input").val()
				if(!$(".sh_add_todo_input").val()){
					alert("Please Enter Title !")
				}else{
					ev.stopPropagation();
					this.saveTodo(todo_input).then(function (rec) {
						$("#accordion").prepend(QWeb.render("ToDoCard", {
							name: todo_input,
							rec:parseInt(rec),
							widget: self,
						}));
					});
					$(".sh_add_todo_input").val("")
			}
			}
		}

		_click_sh_header_pencil(ev) {
            ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_todo_description")[0].style.display = "block";
			ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_todo_label")[0].style.display = "none";
			ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_header_pencil")[0].style.display = "none";
			ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_header_save")[0].style.display = "block";
			var fieldInput = ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_todo_description");
			var fldLength= fieldInput.valueOf().length;
			fieldInput[0].focus()
			fieldInput[0].setSelectionRange(fldLength, fldLength);
		}
		
		_focusout_sh_todo_description(ev) {
			var fieldInput = ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_todo_description");
			ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_header_pencil")[0].style.display = "block";
			ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_header_save")[0].style.display = "none";
			fieldInput[0].style.display = "none";
			ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_todo_label")[0].style.display = "block";
			ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_todo_label")[0].textContent = fieldInput[0].value
			var todo_id  = parseInt(ev.target.getAttribute('ID'))
			this.orm.write("sh.todo", [todo_id], { name : ev.target.parentElement.parentElement.parentElement.parentElement.getElementsByClassName("sh_todo_label")[0].textContent });
		}

		_remove_todo(todo_id) {
			this.removeTodo(todo_id)
		}

		removeTodo(todo_id) {
		    return this.orm.unlink("sh.todo", [todo_id]);
        }

		_close_todo() {
            $('.todo_layout').removeClass('sh_theme_model');
        }

		async saveTodo(todo_input) {
		       var data = await this.orm.create("sh.todo", [{
                       'name': todo_input,
                    }]);
                $(".sh_add_todo_input").val("")
        }

		async _click_add_todo() {
			var self = this;
			var todo_input = $(".sh_add_todo_input").val()
			if(!$(".sh_add_todo_input").val()){
				alert("Please Enter Title !")
			}else{
				await this.saveTodo(todo_input)
				this.onWillStart()
			}
        }

        async add_todo(ev){
            if (ev.which === 13) {
                var self = this;
                var todo_input = $(".sh_add_todo_input").val()
                if(!$(".sh_add_todo_input").val()){
                    alert("Please Enter Title !")
                }else{
                    await this.saveTodo(todo_input)
                    this.onWillStart()
                }

            }

        }

		async doneTodo(done_todo ,todo_id) {
		     await this.orm.write("sh.todo", [todo_id], { is_done : done_todo });
        }

	   async getAllTodo() {
		    const data = await this.orm.searchRead(
            "sh.todo",
            [['user_id', '=', session.uid]],
            ['name','is_done']
            );
            return data
        }

		async _click_sh_todo_checklist(ev) {
			var done_todo = ev.target.checked
			var todo_id  = parseInt(ev.target.id)
			await this.doneTodo(done_todo, todo_id)
			this.onWillStart()
		}
}

registry.category("systray").add("sh_entmate_theme.ToDoWidget", { Component: ToDoWidget }, { sequence: 25 });