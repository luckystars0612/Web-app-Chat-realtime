
DEFAULT_NOTIFICATION_PAGE_SIZE = 5

#general notifications
GENERAL_MSG_TYPE_NOTIFICATIONS_PAYLOAD = 0 #new general notifications data payload incomming
GENERAL_MSG_TYPE_UPDATE_NOTIFICATION = 5 #update a notifcation that has been altered(accept/decline)
GENERAL_MSG_TYPE_PAGINAGION_EXHAUSTED = 1 #no more notifications back to UT
GENERAL_MSG_TYPE_NOTIFICATIONS_REFRESH_PAYLOAD = 2 # refresh notifications
GENERAL_MSG_TYPE_GET_NEW_NOTIFICATIONS = 3 #get new notifications
GENERAL_MSG_TYPE_GET_UNREAD_NOTIFICATIONS_COUNT= 4 #get unread general notifications


#chat notifications
CHAT_MSG_TYPE_NOTIFICATIONS_PAYLOAD = 10 # send unread chat notifications
CHAT_MSG_TYPE_GET_NEW_NOTIFICATIONS = 13 # get new chat notifications
CHAT_MSG_TYPE_PAGINATION_EXHAUSTED = 11 # no more chat notifications
CHAT_MSG_TYPE_GET_UNREAD_NOTIFICATIONS_COUNT = 14 # get the number of notifications