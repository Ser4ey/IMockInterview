import { alpha, createTheme } from '@mui/material/styles';

const brand = {
  ink: '#132018',
  muted: '#52615A',
  primary: '#183827',
  primaryHover: '#2F5D46',
  warm: '#F6F1E8',
  warmLight: '#FBF8F1',
  sage: '#EEF3E8',
  sand: '#F3E7D2',
  line: 'rgba(21, 57, 38, 0.12)',
};

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: brand.primary,
      light: '#355B43',
      dark: '#10281B',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#A97443',
      light: '#F3E7D2',
      dark: '#6C4323',
      contrastText: brand.ink,
    },
    success: {
      main: '#2F6B4F',
    },
    warning: {
      main: '#B7791F',
    },
    background: {
      default: brand.warm,
      paper: brand.warmLight,
    },
    text: {
      primary: brand.ink,
      secondary: brand.muted,
    },
    divider: brand.line,
  },
  typography: {
    fontFamily: ['Bahnschrift', 'Aptos', 'Segoe UI', 'sans-serif'].join(','),
    h1: {
      fontWeight: 800,
      letterSpacing: 0,
      lineHeight: 0.95,
    },
    h2: {
      fontWeight: 800,
      letterSpacing: 0,
      lineHeight: 1,
    },
    h3: {
      fontWeight: 800,
      letterSpacing: 0,
      lineHeight: 1.05,
    },
    h4: {
      fontWeight: 800,
      letterSpacing: 0,
      lineHeight: 1.08,
    },
    h5: {
      fontWeight: 750,
      letterSpacing: 0,
    },
    h6: {
      fontWeight: 750,
      letterSpacing: 0,
    },
    button: {
      fontWeight: 800,
      textTransform: 'none',
      letterSpacing: 0,
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background:
            'radial-gradient(circle at 12% 0%, rgba(177, 213, 190, 0.42), transparent 30%), radial-gradient(circle at 92% 8%, rgba(243, 231, 210, 0.8), transparent 28%), #F6F1E8',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: 42,
          borderRadius: 999,
          boxShadow: 'none',
          paddingInline: 18,
        },
        contained: {
          backgroundColor: brand.primary,
          '&:hover': {
            backgroundColor: brand.primaryHover,
            boxShadow: `0 14px 34px ${alpha(brand.primary, 0.2)}`,
          },
        },
        outlined: {
          borderColor: alpha(brand.primary, 0.22),
          color: brand.primary,
          backgroundColor: alpha('#FFFFFF', 0.45),
          '&:hover': {
            borderColor: alpha(brand.primary, 0.34),
            backgroundColor: alpha(brand.sage, 0.85),
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: `1px solid ${brand.line}`,
          boxShadow: `0 22px 70px ${alpha('#0F172A', 0.08)}`,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: `1px solid ${brand.line}`,
          boxShadow: `0 22px 70px ${alpha('#0F172A', 0.08)}`,
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: 'outlined',
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          backgroundColor: alpha('#FFFFFF', 0.78),
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          fontWeight: 750,
        },
        outlined: {
          borderColor: alpha(brand.primary, 0.2),
          backgroundColor: alpha('#FFFFFF', 0.48),
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 14,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 24,
          backgroundColor: brand.warmLight,
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          height: 9,
          borderRadius: 999,
          backgroundColor: alpha(brand.primary, 0.1),
        },
        bar: {
          borderRadius: 999,
        },
      },
    },
  },
});

export default theme;
