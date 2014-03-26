import tornado.web

class CssModule(tornado.web.UIModule):


    def render(self, fonts, instanceId, folder):
        self.fonts = fonts
        self.instanceId = instanceId
        self.folder = folder
        return ''
        

    def embedded_css(self):

        css = ''
        
        j = 0
        for font in self.fonts: 
        
            css += '''@font-face { 
 font-family: \"'''
            
            css += 'testing{}";\n'.format(j)
            
            css += ' src: url( "{}")'.format(font)
            
            css += ''' format("truetype"); 
}

'''
            
            j+=1

        return css
        

    # def embedded_javascript(self):
#         js = ''
        
#         js += 'var maxTestCases = {};'.format(len(self.fonts))

#         js += '''
# var currentTestCase = 0;
# var interVar;


# function changeFont() {

#         fontFamilyName = "testing";
#         console.log('Call function: ' +currentTestCase + ' style: ' + fontFamilyName + currentTestCase);
#         paras = document.getElementsByTagName("p");


#         for( j=0; j < paras.length; j++ ) {
#                 style = fontFamilyName + currentTestCase ;
#                 console.log(style);
#                 paras[j].style.fontFamily = style;
#         }
#         currentTestCase += 1;
        
#         if( currentTestCase > maxTestCases) {
#                 console.log('Removing timer');
#                 clearInterval(interVar);
# '''
#         js += 'document.location = "/font/{}/{}";'.format(self.instanceId, self.folder)
        
#         js += '''
#         }
# }

# function fire() {
        
#         interVar = setInterval( changeFont, 1000);
# }

# '''

#         return js
