
from flask import session
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, HiddenField, SelectMultipleField, BooleanField, widgets, FieldList, TextField
from wtforms.validators import DataRequired, Email

class MultiCheckboxField(SelectMultipleField):
	widget = widgets.ListWidget(prefix_label=False)
	option_widget = widgets.CheckboxInput()


class EditSelfForm(Form):
	givenname = StringField('Given Name', validators=[DataRequired()])
	surname = StringField('Last Name', validators=[DataRequired()])
	mail = StringField('Preferred E-Mail address', validators=[DataRequired(),Email()])
	send_password = BooleanField('Generate and send new password to user')

	password = StringField('New Password')
	name = StringField('Full Name', validators=[DataRequired()])

	update = SubmitField('Update!')


def get_EditUserForm(group_list):
	class EditUserForm(Form):
		givenname = StringField('Given Name', validators=[DataRequired()])
		surname = StringField('Last Name', validators=[DataRequired()])
		mail = StringField('Preferred E-Mail address', validators=[DataRequired(),Email()])
		send_password = BooleanField('Generate and send new password to user')

		password = StringField('New Password')
		userid = HiddenField('Username', validators=[DataRequired()])
		name = StringField('Full Name', validators=[DataRequired()])

		aliases = StringField('E-Mail aliases')

		groups = MultiCheckboxField('Groups', choices = [ (_.dn,_.name) for _ in group_list ] )

		update = SubmitField('Update!')

		delete_confirm = BooleanField('Confirm deletion')
		delete = SubmitField('Delete!')
	return EditUserForm

def get_NewUserForm(group_list):
	class NewUserForm(Form):
		givenname = StringField('Given Name', validators=[DataRequired()])
		surname = StringField('Last Name', validators=[DataRequired()])
		mail = StringField('Preferred E-Mail address', validators=[DataRequired(),Email()])
		send_password = BooleanField('Generate password and send to user', default=True)

		password = StringField('Password', validators=[DataRequired()])
		userid = StringField('Username', validators=[DataRequired()])
		name = StringField('Full Name', validators=[DataRequired()])

		aliases = StringField('E-Mail aliases')

		groups = MultiCheckboxField('Groups', choices = [ (_.dn,_.name) for _ in group_list ] )

		submit = SubmitField('Create!')

	return NewUserForm

def get_EditGroupForm(user_list):
	class EditGroupForm(Form):
		members = MultiCheckboxField('Members', choices = [ (_.dn,_.name) for _ in user_list ] )

		update = SubmitField('Update!')

		delete_confirm = BooleanField('Confirm deletion')
		delete = SubmitField('Delete!')
	return EditGroupForm

def get_NewGroupForm(user_list):
	class NewGroupForm(Form):
		name = StringField('Group Name', validators=[DataRequired()])

		members = MultiCheckboxField('Members', choices = [ (_.dn,_.name) for _ in user_list ] )

		submit = SubmitField('Create!')

	return NewGroupForm

def get_EditMailingListForm(user_list, group_list):
	class EditMailingListForm(Form):
		list_members = FieldList(StringField(''))

		update = SubmitField('Update!')

		delete_confirm = BooleanField('Confirm deletion')
		delete = SubmitField('Delete!')
	return EditMailingListForm

def get_NewMailingListForm(user_list, group_list):
	class EditMailingListForm(Form):
		name = StringField('Mailing List Name', validators=[DataRequired()])

		list_members = FieldList(StringField(''))

		submit = SubmitField('Create!')
	
	return EditMailingListForm