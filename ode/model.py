from ode import config_get, ldap
from flask import current_app
from ldap3 import STRING_TYPES
import re, flanker.addresslib.address

# Hashes the password value into an {SSHA} password upon setting
class LDAPSSHAPasswordAttribute(ldap.Attribute):
	def __setattr__(self, key, value):
		if key in ['value', '_init']:
			if isinstance(value, STRING_TYPES) and not value.startswith("{"):
				import sha, os
				from base64 import b64encode
				salt = os.urandom(16)
				ctx = sha.new( value )
				ctx.update( salt )
				value = "{SSHA}" + b64encode( ctx.digest() + salt )

		super(LDAPSSHAPasswordAttribute, self).__setattr__(key, value)

class User(ldap.Entry):
	object_classes = ['inetOrgPerson', 'CC-person']
	entry_rdn = ['uid', 'base_dn']

	name = ldap.Attribute('cn')
	userid = ldap.Attribute('uid')
	surname = ldap.Attribute('sn')
	givenname = ldap.Attribute('givenName')
	password = LDAPSSHAPasswordAttribute('userPassword')

	mail = ldap.Attribute('CC-preferredMail')
	_aliases = ldap.Attribute('CC-mailAlias')
	groups = ldap.Attribute('memberOf')

	def save_groups(self, new_groups, group_list):
		add_list = [group for group in group_list if group.dn in new_groups and self.dn not in group.members]
		del_list = [group for group in group_list if group.dn not in new_groups and self.dn in group.members]

		## Since flask_ldapconn sucks with respect to these kinds of modifications
		## we do them ourselves through ldap3

		result = True
		for group in add_list:
			result = group.add_member(self.dn) and result
		for group in del_list:
			result = group.remove_member(self.dn) and result
		return result

	@property
	def aliases(self):
		try:
			return ",".join(self._aliases or [])
		except TypeError:
			return ""
	

	def set_aliases(self, new_aliases):
		self._aliases = [_.strip() for _ in new_aliases.split(",")]

	@property
	def mail_form(self):
		return u"%s <%s>" % (self.name, self.mail)

class Group(ldap.Entry):
	object_classes = ['groupOfNames']
	entry_rdn = ['cn', 'base_dn']

	name = ldap.Attribute('cn')
	members = ldap.Attribute('member')

	def remove_member(self, dn):
		return self.connection.connection.modify(self.dn, {
			"member": [
				("MODIFY_DELETE", [dn])
			]
		})

	def add_member(self, dn):
		return self.connection.connection.modify(self.dn, {
			"member": [
				("MODIFY_ADD", [dn])
			]
		})

	def set_members(self, dnlist):
		add_list = [dn for dn in dnlist if dn not in self.members]
		del_list = [dn for dn in self.members if dn not in dnlist]

		changes = []
		if add_list: changes.append( ("MODIFY_ADD", add_list) )
		if del_list: changes.append( ("MODIFY_DELETE", del_list) )

		if not changes: 
			return True

		return self.connection.connection.modify(self.dn, {
			"member": changes
		})

class MailingList(ldap.Entry):
	object_classes = ['CC-mailingList']
	entry_rdn = ['cn', 'base_dn']

	name = ldap.Attribute('cn')
	members = ldap.Attribute('member', default=[])
	additional_addresses = ldap.Attribute('CC-fullMailAddress', default=[])
	member_urls = ldap.Attribute('CC-memberURL', default=[])

	@property
	def member_urls_group(self):
		return [_ for _ in self.member_urls if self.GROUP_RE.match(_)]

	@property
	def member_urls_user(self):
		return [_ for _ in self.member_urls if self.USER_RE.match(_)]

	@property
	def member_groups(self):
		return [Group.query.get(self.GROUP_RE.match(m).group("group_dn")) for m in self.member_urls_group]
	
	@property
	def member_users(self):
		return [User.query.get(self.USER_RE.match(m).group("user_dn")) for m in self.member_urls_user]

	@property
	def list_members(self):
		return [e.dn for e in self.member_users + self.member_groups] + list(self.additional_addresses)

	def set_list_members(self, new_list_members):
		new_m = set(new_list_members)

		def is_group(dn):
			return dn.endswith(Group.base_dn) \
				and ( self.GROUP_FORMAT % {"group_dn":dn} in self.member_urls \
					or Group.query.get(dn) is not None
				)

		def is_user(dn):
			return dn.endswith(User.base_dn) \
				and ( self.USER_FORMAT % {"user_dn":dn} in self.member_urls \
					or User.query.get(dn) is not None
				)

		def is_either(dn):
			return is_group(dn) or is_user(dn)

		def format_either(dn):
			if is_group(dn):
				return self.GROUP_FORMAT % {"group_dn":dn}
			elif is_user(dn):
				return self.USER_FORMAT % {"user_dn":dn}
			else:
				return dn

		new_additional = set(_ for _ in new_m if not is_either(_))
		new_url = set(format_either(_) for _ in new_m if not _ in new_additional)

		self.additional_addresses = list(new_additional)
		self.member_urls = list(new_url)

	@property
	def as_addresses(self):
		existing_members = [User.query.get(dn) for dn in self.members]
		existing_additional = self.additional_addresses

		existing_addresses = map(flanker.addresslib.address.parse,
				[u.mail_form for u in existing_members]+list(existing_additional)
		)

		return existing_addresses


	def import_list_members(self, import_list):
		import_list = [unicode(i, "UTF-8") if not isinstance(i, unicode) else i for i in import_list]
		current_app.logger.debug("import_list: %s", import_list)

		good, bad = [], []
		for i in import_list:
			a = flanker.addresslib.address.parse(i)
			if a:
				good.append(a)
			else:
				bad.append(i)

		#good, bad = flanker.addresslib.address.parse_list(import_list, as_tuple=True)

		current_app.logger.debug("Good: %s, Bad: %s", good, bad)
		
		existing_addresses = self.as_addresses

		preexisting = []
		notexisting = []
		for a in good:
			if any(e.address == a.address for e in existing_addresses if e):
				preexisting.append(a.to_unicode())
			else:
				notexisting.append(a)

		current_app.logger.debug("preexisting: %s, notexisting: %s", preexisting, notexisting)

		new_users = []
		new_additional = []

		for a in notexisting:
			u = User.query.filter("mail: %s" % a.address).first()

			if u:
				new_users.append(u.dn)
			else:
				new_additional.append(a.to_unicode())

		current_app.logger.debug("new_users: %s, new_additional: %s", new_users, new_additional)

		self.set_list_members( list(self.list_members) + new_users + new_additional )

		return preexisting, bad


def initialize(app):
	User.base_dn = config_get("ODE_USER_BASE", config=app.config)
	Group.base_dn = config_get("ODE_GROUP_BASE", config=app.config)
	MailingList.base_dn = config_get("ODE_MAILING_LIST_BASE", config=app.config)

	def re_to_format(r):
		return re.sub('(^\^)|(\$$)', '', re.sub( '\(\?P<([^>]+)>[^)]+\)', '%(\\1)s', re.sub('\\\\(.)', '\\1', r)) )

	MailingList.USER_RE = re.compile( app.config["MAILING_LIST_MEMBER_USER_TEMPLATE"] )
	MailingList.GROUP_RE = re.compile( app.config["MAILING_LIST_MEMBER_GROUP_TEMPLATE"] % {
		"user_base": re.escape(config_get("ODE_USER_BASE", config=app.config))
	})

	MailingList.USER_FORMAT = re_to_format( app.config["MAILING_LIST_MEMBER_USER_TEMPLATE"] )
	MailingList.GROUP_FORMAT = re_to_format( app.config["MAILING_LIST_MEMBER_GROUP_TEMPLATE"] % {
		"user_base": re.escape(config_get("ODE_USER_BASE", config=app.config))
	})
